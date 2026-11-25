"""`core.storage` sur Garage et PostgreSQL réels (story 1.10), sans aucun mock.

Exige la pile démarrée, l'API S3 de Garage publiée sur l'hôte (`GARAGE_LOCAL_PORT`) et :
- `TEST_S3_ENDPOINT` (ex. `http://127.0.0.1:3900`), `TEST_S3_ACCESS_KEY_ID`,
  `TEST_S3_SECRET_ACCESS_KEY` (fichiers `.env.secrets/s3_*`), `TEST_S3_BUCKET` facultatif ;
- `TEST_APP_DATABASE_URL` : les unités de travail tournent sur la vraie base.

Sans elles, les tests sont ignorés, sauf avec `REQUIRE_INTEGRATION=1` (CI) : ils échouent.
Chaque ligne de la matrice de la story est vérifiée par relecture de l'objet et comptage
du bucket. L'horloge est fixée en février 2031 : les objets de test sont faciles à
reconnaître, et tous sont supprimés en fin de test.
"""

import hashlib
import io
import os
import re
import urllib.error
import urllib.request
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import boto3
import pytest
from botocore.config import Config
from botocore.exceptions import ClientError
from PIL import Image
from sqlalchemy import make_url, text

from app.core import clock, db, storage
from app.core.config import get_settings
from app.core.db import current_session, unit_of_work
from app.core.enums import PhotoKind
from app.core.errors import DomainError, ErrorCode
from tests import photos

pytestmark = pytest.mark.integration

DEFAULT_BUCKET = "terangacycle-photos"
FIXED_NOW = datetime(2031, 2, 14, 10, 30, tzinfo=UTC)
TEST_PREFIXES = tuple(f"{kind}/2031/02/" for kind in PhotoKind)
UUID4 = r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"
KEY = re.compile(rf"report/2031/02/{UUID4}\.jpg")


class Boom(Exception):
    pass


def _env(var: str) -> str:
    value = os.environ.get(var, "").strip()
    if not value:
        pytest.skip(f"{var} non défini : tests d'intégration du stockage ignorés")
    return value


@dataclass
class Garage:
    """Accès de contrôle au bucket (relecture, comptage), indépendant de core.storage."""

    client: Any
    endpoint: str
    bucket: str

    def keys(self) -> list[str]:
        """Objets des préfixes de test seulement (horloge fixée) : d'autres écrivains
        peuvent travailler dans le même bucket."""
        paginator = self.client.get_paginator("list_objects_v2")
        return [
            item["Key"]
            for prefix in TEST_PREFIXES
            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix)
            for item in page.get("Contents", [])
        ]

    def count(self) -> int:
        return len(self.keys())

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("404", "NoSuchKey", "NotFound"):
                return False
            raise
        return True

    def read(self, key: str) -> dict[str, Any]:
        return self.client.get_object(Bucket=self.bucket, Key=key)


@pytest.fixture
def garage(monkeypatch: pytest.MonkeyPatch) -> Iterator[Garage]:
    endpoint = _env("TEST_S3_ENDPOINT")
    access_key = _env("TEST_S3_ACCESS_KEY_ID")
    secret_key = _env("TEST_S3_SECRET_ACCESS_KEY")
    bucket = os.environ.get("TEST_S3_BUCKET", "").strip() or DEFAULT_BUCKET
    region = os.environ.get("TEST_S3_REGION", "").strip() or "garage"
    database_url = make_url(_env("TEST_APP_DATABASE_URL"))
    if database_url.drivername in ("postgresql", "postgres"):
        database_url = database_url.set(drivername="postgresql+psycopg")

    # core.storage et core.db lisent leurs réglages dans Settings (environnement).
    monkeypatch.setenv("S3_ENDPOINT", endpoint)
    monkeypatch.setenv("S3_ACCESS_KEY_ID", access_key)
    monkeypatch.setenv("S3_SECRET_ACCESS_KEY", secret_key)
    monkeypatch.setenv("S3_BUCKET", bucket)
    monkeypatch.setenv("S3_REGION", region)
    monkeypatch.setenv("DATABASE_URL", database_url.render_as_string(hide_password=False))
    monkeypatch.setattr(clock, "now", lambda: FIXED_NOW)
    caches = (get_settings, db.get_engine, db.get_sessionmaker, storage._s3_client)
    for cache in caches:
        cache.cache_clear()

    client = boto3.session.Session().client(
        "s3",
        endpoint_url=endpoint,
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(
            s3={"addressing_style": "path"},
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
        ),
    )
    target = Garage(client=client, endpoint=endpoint.rstrip("/"), bucket=bucket)
    try:
        yield target
    finally:
        try:
            # Nettoyage des seuls préfixes de test ; un échec n'arrête pas les suivants.
            for key in target.keys():
                try:
                    client.delete_object(Bucket=bucket, Key=key)
                except Exception as exc:
                    print(f"nettoyage impossible : {key} ({type(exc).__name__})")
        finally:
            try:
                db.get_engine().dispose()
            finally:
                for cache in caches:
                    cache.cache_clear()


def _ingest(garage: Garage, data: bytes, kind: PhotoKind = PhotoKind.REPORT) -> storage.StoredPhoto:
    """Stocke une photo dans une unité de travail validée sur la vraie base."""
    with unit_of_work():
        current_session().execute(text("SELECT 1"))
        stored = storage.ingest_photo(kind, data)
    return stored


def _stored_image(garage: Garage, key: str) -> tuple[bytes, dict[str, Any]]:
    response = garage.read(key)
    return response["Body"].read(), response


def _refused(garage: Garage, data: bytes) -> DomainError:
    before = garage.count()
    with pytest.raises(DomainError) as exc_info, unit_of_work():
        current_session().execute(text("SELECT 1"))
        storage.ingest_photo(PhotoKind.REPORT, data)
    assert garage.count() == before, "objet écrit pour une photo refusée"
    return exc_info.value


# --- Photos acceptées ---------------------------------------------------------------


def test_jpeg_with_exif_gps_and_orientation_is_stored_clean(garage: Garage) -> None:
    received = photos.jpeg_with_metadata((4000, 3000))
    assert len(received) < storage.MAX_PHOTO_BYTES
    before = garage.count()

    stored = _ingest(garage, received)

    assert garage.count() == before + 1
    assert KEY.fullmatch(stored.object_key), stored.object_key
    assert stored.sha256 == hashlib.sha256(received).hexdigest()
    assert (stored.width, stored.height) == (3000, 4000)
    body, response = _stored_image(garage, stored.object_key)
    assert response["ContentType"] == "image/jpeg"
    assert response.get("Metadata", {}) == {}
    assert not set(photos.jpeg_markers(body)) & photos.METADATA_MARKERS
    for marker in (photos.CAMERA_MAKE.encode(), photos.XMP_MARKER, photos.COMMENT_MARKER):
        assert marker not in body
    with Image.open(io.BytesIO(body)) as image:
        assert image.format == "JPEG" and image.size == (3000, 4000)
        assert len(image.getexif()) == 0
        assert not {"exif", "icc_profile", "xmp", "comment"} & image.info.keys()


def test_transparent_png_is_stored_as_jpeg_on_white(garage: Garage) -> None:
    stored = _ingest(garage, photos.png_transparent((64, 48)))
    body, response = _stored_image(garage, stored.object_key)
    assert response["ContentType"] == "image/jpeg"
    with Image.open(io.BytesIO(body)) as image:
        assert image.format == "JPEG" and image.mode == "RGB" and image.size == (64, 48)
        background = image.getpixel((60, 44))
    assert isinstance(background, tuple) and min(background) >= 245, background


def test_webp_is_stored_as_jpeg(garage: Garage) -> None:
    received = photos.encoded("WEBP", (120, 80))
    stored = _ingest(garage, received)
    body, _ = _stored_image(garage, stored.object_key)
    with Image.open(io.BytesIO(body)) as image:
        assert image.format == "JPEG" and image.size == (120, 80)
    assert stored.sha256 == hashlib.sha256(received).hexdigest()


def test_proof_kind_has_its_own_prefix(garage: Garage) -> None:
    stored = _ingest(garage, photos.encoded("JPEG"), PhotoKind.PROOF)
    assert stored.object_key.startswith("proof/2031/02/")
    assert garage.exists(stored.object_key)


# --- Photos refusées : aucun objet ---------------------------------------------------


def test_too_large_is_413_without_object(garage: Garage) -> None:
    data = photos.encoded("PNG")
    data += b"\x00" * (storage.MAX_PHOTO_BYTES + 1 - len(data))
    assert len(data) == 1_048_577
    error = _refused(garage, data)
    assert (error.code, error.http_status) == (ErrorCode.PHOTO_TOO_LARGE, 413)


@pytest.mark.parametrize(
    "data",
    [photos.encoded("GIF"), b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n1 0 obj\n", b"texte renomme en .jpg\n"],
    ids=["gif", "pdf", "texte-renomme"],
)
def test_other_format_is_415_without_object(garage: Garage, data: bytes) -> None:
    error = _refused(garage, data)
    assert (error.code, error.http_status) == (ErrorCode.UNSUPPORTED_MEDIA_TYPE, 415)


def test_too_many_pixels_is_422_without_object(garage: Garage) -> None:
    error = _refused(garage, photos.png_header_only(5000, 5000))
    assert (error.code, error.http_status) == (ErrorCode.PHOTO_TOO_MANY_PIXELS, 422)


def test_corrupted_is_422_without_object(garage: Garage) -> None:
    error = _refused(garage, b"\xff\xd8\xff\xe0" + os.urandom(4096))
    assert (error.code, error.http_status) == (ErrorCode.PHOTO_UNREADABLE, 422)


# --- Transactions -------------------------------------------------------------------


def test_rollback_deletes_the_object(garage: Garage) -> None:
    before = garage.count()
    with pytest.raises(Boom), unit_of_work():
        current_session().execute(text("SELECT 1"))
        stored = storage.ingest_photo(PhotoKind.REPORT, photos.encoded("JPEG"))
        assert garage.exists(stored.object_key)  # écrit pendant l'unité
        assert garage.count() == before + 1
        raise Boom
    assert garage.count() == before
    assert not garage.exists(stored.object_key)


def test_purge_deletes_after_commit(garage: Garage) -> None:
    stored = _ingest(garage, photos.encoded("JPEG"))
    before = garage.count()
    with unit_of_work():
        current_session().execute(text("SELECT 1"))
        storage.purge([stored.object_key])
        assert garage.exists(stored.object_key)  # rien avant le commit
    assert not garage.exists(stored.object_key)
    assert garage.count() == before - 1


def test_purge_keeps_the_object_after_rollback(garage: Garage) -> None:
    stored = _ingest(garage, photos.encoded("JPEG"))
    before = garage.count()
    with pytest.raises(Boom), unit_of_work():
        current_session().execute(text("SELECT 1"))
        storage.purge([stored.object_key])
        raise Boom
    assert garage.exists(stored.object_key)
    assert garage.count() == before


def test_purge_of_a_missing_object_is_not_an_error(
    garage: Garage, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = "report/2031/02/00000000-0000-4000-8000-000000000000.jpg"
    assert not garage.exists(missing)
    with unit_of_work():
        storage.purge([missing])
    out = capsys.readouterr().out
    assert "photo_purged_failed" not in out and '"event": "photo_purged"' in out


# --- Bucket privé -------------------------------------------------------------------


@pytest.mark.parametrize("method", ["GET", "HEAD"])
def test_anonymous_read_is_refused(garage: Garage, method: str) -> None:
    stored = _ingest(garage, photos.encoded("JPEG"))
    url = f"{garage.endpoint}/{garage.bucket}/{stored.object_key}"
    request = urllib.request.Request(url, method=method)  # noqa: S310 (endpoint de test)
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(request, timeout=5)  # noqa: S310 (endpoint de test)
    assert exc_info.value.code == 403
    assert garage.exists(stored.object_key)  # l'objet existe bien : refus d'accès
