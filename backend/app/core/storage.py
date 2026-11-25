"""Stockage des photos dans le bucket privé Garage (AD-13, story 1.10).

Seul module de l'application qui parle S3 (la sonde `/readyz` de `core.health` garde
son propre client). Deux fonctions, appelées dans une unité de travail (`core.db`) :

- `ingest_photo(kind, data)` contrôle les octets reçus, dans l'ordre : poids (413
  `photo_too_large`), format reconnu à sa signature (415 `unsupported_media_type`),
  largeur × hauteur lues dans l'en-tête sans décoder (422 `photo_too_many_pixels`),
  décodage (422 `photo_unreadable`). Elle ré-encode ensuite l'image en JPEG sans aucune
  métadonnée (orientation EXIF appliquée, transparence sur fond blanc) et la stocke sous
  `<kind>/<aaaa>/<mm>/<uuid>.jpg`. Si l'unité de travail est annulée, l'objet est supprimé.
- `purge(object_keys)` supprime des objets, seulement après le commit.

Confidentialité : ni octets ni métadonnées dans les journaux ; un journal de stockage ne
porte que la clé de l'objet.
"""

import asyncio
import hashlib
import io
import re
import threading
import uuid
import warnings
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from PIL import Image, ImageCms, ImageMath, ImageOps

from app.core import clock
from app.core.config import get_settings
from app.core.db import _require_uow, after_commit, after_rollback
from app.core.enums import PhotoKind
from app.core.errors import DomainError, ErrorCode
from app.core.logging import get_logger

log = get_logger(__name__)

# Plafonds de la photo reçue (FR-3) : poids en octets, largeur × hauteur en pixels.
MAX_PHOTO_BYTES = 1_048_576
MAX_PHOTO_PIXELS = 12_000_000
JPEG_QUALITY = 85
CONTENT_TYPE = "image/jpeg"

# Garde de Pillow contre les bombes de décompression, réglée sur le même plafond : au-delà
# du double, `Image.open` refuse l'image dès l'en-tête (DecompressionBombError).
Image.MAX_IMAGE_PIXELS = MAX_PHOTO_PIXELS

# Délais du client de stockage : une photo d'au plus 1 Mo, sur le réseau Compose.
S3_CONNECT_TIMEOUT_S = 3
S3_READ_TIMEOUT_S = 10
S3_MAX_ATTEMPTS = 3

# Signatures acceptées → nom du format dans Pillow.
_JPEG = "JPEG"
_PNG = "PNG"
_WEBP = "WEBP"
# Formats que Pillow peut lire pour chaque signature : un JPEG de smartphone portant un
# index MPF (photos multiples) s'ouvre en « MPO » ; seule la première image est gardée.
_PILLOW_FORMATS = {_JPEG: {"JPEG", "MPO"}, _PNG: {"PNG"}, _WEBP: {"WEBP"}}
# Modes 16 bits (PNG en niveaux de gris 16 bits) : ramenés à 8 bits avant le RVB.
_WIDE_MODES = frozenset({"I", "I;16", "I;16L", "I;16B", "I;16N"})
_SRGB = ImageCms.createProfile("sRGB")

# Clé produite par `object_key_for` : seule forme acceptée par `purge`.
_OBJECT_KEY = re.compile(
    "(?:" + "|".join(re.escape(kind.value) for kind in PhotoKind) + ")"
    r"/[0-9]{4}/[0-9]{2}/[0-9a-f-]{36}\.jpg"
)


@dataclass(frozen=True, slots=True)
class StoredPhoto:
    """Photo stockée : clé dans le bucket, empreinte des octets reçus, taille stockée."""

    object_key: str
    # SHA-256 (hexadécimal) des octets reçus, avant ré-encodage : détection de photo
    # identique (story 1.14).
    sha256: str
    width: int
    height: int


# --- Contrôles ----------------------------------------------------------------------


def detect_format(data: bytes) -> str | None:
    """Format reconnu à la signature des octets (JPEG, PNG, WebP), sinon None.

    Jamais d'après le nom du fichier ni le type annoncé par le client.
    """
    if data.startswith(b"\xff\xd8\xff"):
        return _JPEG
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return _PNG
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return _WEBP
    return None


def _unreadable() -> DomainError:
    return DomainError(ErrorCode.PHOTO_UNREADABLE, 422)


def _open_checked(data: bytes) -> Image.Image:
    """Image ouverte (en-tête lu, pixels non décodés) après les contrôles de poids, de
    format et de nombre de pixels, dans cet ordre."""
    if len(data) > MAX_PHOTO_BYTES:
        raise DomainError(ErrorCode.PHOTO_TOO_LARGE, 413)
    expected = detect_format(data)
    if expected is None:
        raise DomainError(ErrorCode.UNSUPPORTED_MEDIA_TYPE, 415)
    try:
        # Seul le décodeur de la signature est essayé : `Image.open` ne lit que l'en-tête.
        # Entre 12 et 24 Mpx, Pillow avertit seulement : le contrôle ci-dessous refuse.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", Image.DecompressionBombWarning)
            image = Image.open(io.BytesIO(data), formats=[expected])
    except Image.DecompressionBombError:
        raise DomainError(ErrorCode.PHOTO_TOO_MANY_PIXELS, 422) from None
    except Exception:
        # Signature reconnue, en-tête illisible.
        raise _unreadable() from None
    if image.format not in _PILLOW_FORMATS[expected]:
        image.close()
        raise DomainError(ErrorCode.UNSUPPORTED_MEDIA_TYPE, 415)
    width, height = image.size
    if width * height > MAX_PHOTO_PIXELS:
        image.close()
        raise DomainError(ErrorCode.PHOTO_TOO_MANY_PIXELS, 422)
    return image


def _upright(image: Image.Image) -> Image.Image:
    """Orientation EXIF appliquée ; un EXIF illisible laisse l'image telle quelle."""
    try:
        return ImageOps.exif_transpose(image)
    except Exception:
        return image


def _to_srgb(image: Image.Image) -> Image.Image:
    """Pixels convertis vers sRGB si un profil ICC est joint (il ne sera pas stocké).

    Profil illisible ou conversion impossible : pixels gardés tels quels.
    """
    icc = image.info.get("icc_profile")
    if not icc or "transparency" in image.info:
        return image
    try:
        source = ImageCms.ImageCmsProfile(io.BytesIO(icc))
        mode = "RGBA" if "A" in image.getbands() else "RGB"
        converted = ImageCms.profileToProfile(image, source, _SRGB, outputMode=mode)
    except Exception:
        return image
    return converted or image


def _flatten(image: Image.Image) -> Image.Image:
    """Image RVB neuve (aucune `info` héritée) ; une transparence devient un fond blanc."""
    alpha: Image.Image | None = None
    transparent = image.info.get("transparency")
    if image.mode in _WIDE_MODES:
        wide = image.convert("I")
        if transparent is not None:
            alpha = ImageMath.lambda_eval(lambda a: (a["v"] != transparent) * 255, v=wide)
            alpha = alpha.convert("L")
        image = wide.point(lambda v: v * (1 / 256)).convert("L")
    elif "A" in image.getbands() or transparent is not None:
        image = image.convert("RGBA")
        alpha = image.getchannel("A")
    canvas = Image.new("RGB", image.size, (255, 255, 255))
    canvas.paste(image.convert("RGB"), mask=alpha)
    return canvas


def reencode(data: bytes) -> tuple[bytes, int, int]:
    """Contrôle les octets reçus et renvoie (JPEG sans métadonnée, largeur, hauteur).

    Lève `DomainError` (413, 415 ou 422) si la photo est refusée.
    """
    with _open_checked(data) as image:
        try:
            image.load()
            clean = _flatten(_to_srgb(_upright(image)))
            out = io.BytesIO()
            # Image neuve, sans `info` : ni EXIF, ni profil ICC, ni XMP, ni commentaire.
            clean.save(out, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        except Exception:
            raise _unreadable() from None
    return out.getvalue(), clean.width, clean.height


# --- Client S3 ----------------------------------------------------------------------


@lru_cache
def _s3_session() -> boto3.session.Session:
    # Session dédiée : la session par défaut de boto3 n'est pas sûre entre threads.
    return boto3.session.Session()


@lru_cache
def _s3_client(endpoint: str, region: str, access_key: str, secret_key: str) -> Any:
    # Client du stockage, distinct de celui de la sonde : path-style et sommes de contrôle
    # seulement si exigées (Garage), délais raisonnables et quelques nouveaux essais.
    return _s3_session().client(
        "s3",
        endpoint_url=endpoint,
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
            connect_timeout=S3_CONNECT_TIMEOUT_S,
            read_timeout=S3_READ_TIMEOUT_S,
            retries={"total_max_attempts": S3_MAX_ATTEMPTS, "mode": "standard"},
        ),
    )


# La création d'un client (lru_cache, session boto3 partagée) n'est pas sûre entre threads.
_client_lock = threading.Lock()


def _client_and_bucket() -> tuple[Any, str]:
    settings = get_settings()
    if settings.s3_access_key_id is None or settings.s3_secret_access_key is None:
        raise RuntimeError("Stockage non configuré : identifiants S3 absents.")
    with _client_lock:
        client = _s3_client(
            settings.s3_endpoint,
            settings.s3_region,
            settings.s3_access_key_id.get_secret_value(),
            settings.s3_secret_access_key.get_secret_value(),
        )
    return client, settings.s3_bucket


def _put(object_key: str, body: bytes) -> None:
    client, bucket = _client_and_bucket()
    # Aucun ACL : le bucket est privé, l'objet aussi.
    client.put_object(Bucket=bucket, Key=object_key, Body=body, ContentType=CONTENT_TYPE)


def _delete(object_key: str) -> None:
    """Supprime un objet ; un objet absent n'est pas une erreur."""
    client, bucket = _client_and_bucket()
    try:
        client.delete_object(Bucket=bucket, Key=object_key)
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") not in ("NoSuchKey", "404"):
            raise


def _delete_all(object_keys: tuple[str, ...], event: str) -> None:
    # Un échec n'empêche pas les suppressions suivantes ; seule la clé est journalisée.
    for object_key in object_keys:
        try:
            _delete(object_key)
        except Exception as exc:
            log.warning(f"{event}_failed", object_key=object_key, reason=type(exc).__name__)
        else:
            log.info(event, object_key=object_key)


# --- Hooks de transaction -----------------------------------------------------------


async def _in_thread(fn: Callable[..., None], *args: Any) -> None:
    await asyncio.to_thread(fn, *args)


def _register(register: Callable[..., None], fn: Callable[..., None], *args: Any) -> None:
    """Enregistre un effet S3 ; dans une unité asynchrone, il part dans le pool de
    threads pour ne pas bloquer la boucle asyncio."""
    if _require_uow().is_async:
        register(_in_thread, fn, *args)
    else:
        register(fn, *args)


# --- API du module ------------------------------------------------------------------


def object_key_for(kind: PhotoKind) -> str:
    """Clé neuve `<kind>/<aaaa>/<mm>/<uuid4>.jpg`, année et mois UTC de `core.clock`."""
    moment = clock.now()
    return f"{PhotoKind(kind).value}/{moment:%Y}/{moment:%m}/{uuid.uuid4()}.jpg"


def ingest_photo(kind: PhotoKind, data: bytes) -> StoredPhoto:
    """Contrôle, nettoie et stocke une photo reçue, dans l'unité de travail en cours.

    Lève `DomainError` si la photo est refusée (413, 415, 422 ; aucun objet n'est alors
    écrit) ou si le stockage échoue (503 `storage_unavailable`), et `RuntimeError` hors
    d'une unité de travail. L'objet est supprimé si l'unité est annulée.

    Fonction bloquante : depuis la boucle asyncio, appeler `ingest_photo_async`.
    """
    _require_uow()
    kind = PhotoKind(kind)
    body, width, height = reencode(data)
    digest = hashlib.sha256(data).hexdigest()
    object_key = object_key_for(kind)
    # Nettoyage enregistré avant l'écriture : une écriture faite mais signalée en échec
    # (délai dépassé) ne laisse pas d'objet orphelin si l'unité est annulée.
    _register(after_rollback, _delete_all, (object_key,), "photo_rollback_deleted")
    try:
        _put(object_key, body)
    except Exception as exc:
        # Écriture peut-être faite : supprimée aussi si l'appelant valide malgré l'erreur.
        _register(after_commit, _delete_all, (object_key,), "photo_orphan_deleted")
        log.warning("photo_store_failed", object_key=object_key, reason=type(exc).__name__)
        raise DomainError(ErrorCode.STORAGE_UNAVAILABLE, 503) from exc
    log.info("photo_stored", object_key=object_key)
    return StoredPhoto(object_key=object_key, sha256=digest, width=width, height=height)


async def ingest_photo_async(kind: PhotoKind, data: bytes) -> StoredPhoto:
    """`ingest_photo` dans le pool de threads, pour une unité de travail asynchrone.

    Le contexte (donc l'unité de travail en cours) est copié dans le thread.
    """
    return await asyncio.to_thread(ingest_photo, kind, data)


def purge(object_keys: Iterable[str]) -> None:
    """Supprime des objets du bucket après le commit de l'unité de travail en cours.

    Rien n'est supprimé si l'unité est annulée. `RuntimeError` hors d'une unité de
    travail, `TypeError` pour une chaîne seule, `ValueError` pour une clé qui n'a pas la
    forme `<kind>/<aaaa>/<mm>/<uuid>.jpg`.
    """
    _require_uow()
    if isinstance(object_keys, str | bytes):
        raise TypeError("purge attend une collection de clés, pas une chaîne.")
    keys = tuple(object_keys)
    if any(not isinstance(key, str) or not _OBJECT_KEY.fullmatch(key) for key in keys):
        raise ValueError("Clé d'objet invalide.")
    if keys:
        _register(after_commit, _delete_all, keys, "photo_purged")
