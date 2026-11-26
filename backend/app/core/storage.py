"""Stockage objet des photos (AD-13) : seul module qui écrit dans le bucket S3 (Garage).

- `ingest_photo(kind, data)` contrôle les octets reçus, les ré-encode en JPEG sans
  aucune métadonnée et range l'objet dans le bucket privé. Il exige une unité de
  travail : si elle est annulée, l'objet écrit est supprimé (`after_rollback`).
- `purge(object_keys)` supprime des objets, seulement après le commit (`after_commit`).

Contrôles, dans cet ordre et tous avant l'écriture S3 :
1. plus de 1 Mo → 413 `photo_too_large` ;
2. type lu dans les octets (JPEG, PNG, WebP), jamais le nom ni le Content-Type
   → 415 `unsupported_media_type` ;
3. plus de 12 Mpx, lu dans l'en-tête avant décodage → 422 `photo_too_many_pixels` ;
4. décodage impossible ou tronqué → 422 `photo_unreadable`.

Aucun octet de photo, clé ni identifiant dans les messages d'erreur ; le journal ne
porte que le type d'exception.
"""

import asyncio
import hashlib
import io
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from PIL import Image, ImageOps

from app.core.clock import now
from app.core.config import get_settings
from app.core.db import after_commit, after_rollback, current_session
from app.core.enums import PhotoKind
from app.core.errors import DomainError, ErrorCode
from app.core.logging import get_logger

log = get_logger(__name__)

MAX_PHOTO_BYTES = 1_000_000
MAX_PHOTO_PIXELS = 12_000_000
JPEG_QUALITY = 85
CONTENT_TYPE = "image/jpeg"

# Réglage explicite du garde-fou de Pillow contre les bombes de décompression (global au
# processus, exigé par AD-13) : au-delà, Pillow avertit seulement ; au-delà du double, il
# refuse d'ouvrir (DecompressionBombError). Le refus à 12 Mpx exactement est le contrôle
# explicite de `_decode`, qui ne touche pas à l'état global des avertissements.
Image.MAX_IMAGE_PIXELS = MAX_PHOTO_PIXELS

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


@dataclass(frozen=True)
class StoredPhoto:
    """Photo rangée dans le bucket. `sha256` est celui des octets reçus, avant ré-encodage."""

    photo_id: uuid.UUID
    object_key: str
    sha256: str
    width: int
    height: int


# --- Contrôle et ré-encodage --------------------------------------------------------


def sniff_format(data: bytes) -> str | None:
    """Format Pillow lu dans les premiers octets (JPEG, PNG ou WEBP), sinon None."""
    if data.startswith(b"\xff\xd8\xff"):
        return "JPEG"
    if data.startswith(_PNG_SIGNATURE):
        return "PNG"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "WEBP"
    return None


def _too_many_pixels() -> DomainError:
    return DomainError(ErrorCode.PHOTO_TOO_MANY_PIXELS, 422)


def _unreadable() -> DomainError:
    return DomainError(ErrorCode.PHOTO_UNREADABLE, 422)


def _decode(data: bytes, fmt: str) -> Image.Image:
    """Ouvre l'image avec le seul décodeur du format détecté, pixels vérifiés avant décodage."""
    try:
        # Image.open ne lit que l'en-tête : la taille est connue avant tout décodage.
        image = Image.open(io.BytesIO(data), formats=[fmt])
    except Image.DecompressionBombError:
        raise _too_many_pixels() from None
    except Exception:
        raise _unreadable() from None
    if image.width * image.height > MAX_PHOTO_PIXELS:
        raise _too_many_pixels()
    try:
        image.load()
        return ImageOps.exif_transpose(image)
    except Image.DecompressionBombError:
        raise _too_many_pixels() from None
    except Exception:
        # Fichier tronqué, données corrompues, EXIF illisible : rien n'est gardé.
        raise _unreadable() from None


def _to_clean_rgb(image: Image.Image) -> Image.Image:
    """Copie RGB sans aucune métadonnée ; la transparence est posée sur fond blanc."""
    # Canal alpha, ou couleur transparente (tRNS) d'une palette, d'un RGB ou d'un gris.
    has_alpha = image.mode in ("RGBA", "LA", "PA") or "transparency" in image.info
    if has_alpha:
        rgba = image.convert("RGBA")
        rgb = Image.new("RGB", rgba.size, (255, 255, 255))
        rgb.paste(rgba, mask=rgba.getchannel("A"))
    else:
        rgb = image.convert("RGB")
    # `info` vidé : ni EXIF, ni ICC, ni XMP, ni commentaire ne peuvent être recopiés à
    # l'enregistrement (Pillow relit `info` pour certains d'entre eux).
    rgb.info = {}
    return rgb


def sanitize_photo(data: bytes) -> tuple[bytes, int, int]:
    """Contrôle `data` et renvoie (JPEG sans métadonnées, largeur, hauteur).

    Lève `DomainError` (413, 415 ou 422) ; aucune écriture n'a lieu ici.
    """
    if len(data) > MAX_PHOTO_BYTES:
        raise DomainError(ErrorCode.PHOTO_TOO_LARGE, 413)
    fmt = sniff_format(data)
    if fmt is None:
        raise DomainError(ErrorCode.UNSUPPORTED_MEDIA_TYPE, 415)
    clean = _to_clean_rgb(_decode(data, fmt))
    out = io.BytesIO()
    clean.save(out, "JPEG", quality=JPEG_QUALITY, optimize=True)
    return out.getvalue(), clean.width, clean.height


def object_key(kind: PhotoKind, photo_id: uuid.UUID) -> str:
    """Clé `<kind>/<yyyy>/<mm>/<uuid>.jpg`, mois UTC de l'horloge du serveur."""
    at = now()
    return f"{kind.value}/{at:%Y}/{at:%m}/{photo_id}.jpg"


# --- Client S3 ----------------------------------------------------------------------


@lru_cache
def _s3_session() -> boto3.session.Session:
    # Session dédiée : la session par défaut de boto3 n'est pas sûre entre threads.
    return boto3.session.Session()


@lru_cache
def _s3_client(endpoint: str, region: str, access_key: str, secret_key: str) -> Any:
    # Configuration explicite pour Garage (AD-13) : s3v4, path-style, sommes de contrôle
    # seulement si exigées ; délais bornés pour ne pas retenir une requête.
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
            connect_timeout=3,
            read_timeout=10,
            retries={"total_max_attempts": 3, "mode": "standard"},
        ),
    )


def _client_and_bucket() -> tuple[Any, str]:
    settings = get_settings()
    if settings.s3_access_key_id is None or settings.s3_secret_access_key is None:
        raise RuntimeError("Identifiants S3 absents.")
    client = _s3_client(
        settings.s3_endpoint,
        settings.s3_region,
        settings.s3_access_key_id.get_secret_value(),
        settings.s3_secret_access_key.get_secret_value(),
    )
    return client, settings.s3_bucket


def _delete(key: str) -> None:
    """Supprime un objet ; un objet déjà absent n'est pas une erreur. Ne lève jamais."""
    try:
        client, bucket = _client_and_bucket()
        client.delete_object(Bucket=bucket, Key=key)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        if code not in ("NoSuchKey", "404"):
            log.warning("storage_delete_failed", reason=f"ClientError:{code}")
    except Exception as exc:
        # Ni clé ni message (il peut contenir l'URL) : le type seulement.
        log.warning("storage_delete_failed", reason=type(exc).__name__)


def _delete_all(keys: tuple[str, ...]) -> None:
    # Objet par objet : DeleteObjects exige une somme de contrôle (support Garage non vérifié).
    for key in keys:
        _delete(key)


def _off_loop(fn: Any, *args: Any) -> Any:
    """Effet bloquant d'une unité de travail : appelé directement hors boucle asyncio ;
    dans une unité pilotée par la boucle (requête HTTP), renvoyé comme coroutine exécutée
    dans un thread, que l'unité attend (jamais d'appel S3 bloquant sur la boucle)."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return fn(*args)
    return asyncio.to_thread(fn, *args)


# --- API du module --------------------------------------------------------------


def ingest_photo(
    kind: PhotoKind | str, data: bytes, photo_id: uuid.UUID | None = None
) -> StoredPhoto:
    """Contrôle, nettoie et range une photo dans le bucket privé.

    À appeler dans une unité de travail : l'objet est supprimé si elle est annulée.
    `photo_id` est l'identifiant de la future ligne photo (généré s'il manque). Il doit
    être neuf : un identifiant déjà stocké écraserait l'objet existant, et un rollback le
    supprimerait.
    """
    current_session()  # RuntimeError s'il n'y a aucune unité de travail en cours.
    kind = PhotoKind(kind)
    jpeg, width, height = sanitize_photo(data)
    digest = hashlib.sha256(data).hexdigest()  # octets reçus, une fois le poids contrôlé
    photo_id = photo_id or uuid.uuid4()
    key = object_key(kind, photo_id)
    client, bucket = _client_and_bucket()
    # Nettoyage enregistré avant l'envoi : une écriture partielle est aussi effacée.
    after_rollback(_off_loop, _delete, key)
    client.put_object(Bucket=bucket, Key=key, Body=jpeg, ContentType=CONTENT_TYPE)
    return StoredPhoto(photo_id=photo_id, object_key=key, sha256=digest, width=width, height=height)


# --- Note vocale ----------------------------------------------------------------------

# 30 s en Opus à 32 kbit/s font environ 120 Ko : 600 Ko laisse la marge des encodeurs.
MAX_VOICE_BYTES = 600_000
VOICE_KIND = "voice"


@dataclass(frozen=True)
class StoredVoice:
    object_key: str
    sha256: str
    size: int
    content_type: str


def sniff_voice(data: bytes) -> tuple[str, str] | None:
    """(extension, type MIME) lus dans les octets : WebM, Ogg ou MP4 ; sinon None."""
    if data.startswith(b"\x1a\x45\xdf\xa3"):
        return "webm", "audio/webm"
    if data.startswith(b"OggS"):
        return "ogg", "audio/ogg"
    if len(data) >= 12 and data[4:8] == b"ftyp":
        return "m4a", "audio/mp4"
    return None


def ingest_voice(data: bytes, voice_id: uuid.UUID | None = None) -> StoredVoice:
    """Contrôle et range une note vocale dans le bucket privé (dans une unité de travail).

    Refus avant toute écriture : plus de 600 Ko → 413 `voice_too_large` ; ni WebM, ni Ogg,
    ni MP4 d'après les octets → 415 `unsupported_voice_type`. L'audio n'est pas
    ré-encodé : ces conteneurs ne portent ni position ni identité de l'appareil.
    """
    current_session()
    if len(data) > MAX_VOICE_BYTES:
        raise DomainError(ErrorCode.VOICE_TOO_LARGE, 413)
    sniffed = sniff_voice(data)
    if sniffed is None:
        raise DomainError(ErrorCode.UNSUPPORTED_VOICE_TYPE, 415)
    extension, content_type = sniffed
    at = now()
    key = f"{VOICE_KIND}/{at:%Y}/{at:%m}/{voice_id or uuid.uuid4()}.{extension}"
    client, bucket = _client_and_bucket()
    after_rollback(_off_loop, _delete, key)
    client.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)
    return StoredVoice(
        object_key=key,
        sha256=hashlib.sha256(data).hexdigest(),
        size=len(data),
        content_type=content_type,
    )


def purge(object_keys: Iterable[str]) -> None:
    """Supprime ces objets après le commit de l'unité de travail en cours, jamais avant."""
    current_session()
    if isinstance(object_keys, str | bytes):
        raise TypeError("purge attend une liste de clés, pas une clé seule.")
    keys = tuple(object_keys)
    if keys:
        after_commit(_off_loop, _delete_all, keys)
