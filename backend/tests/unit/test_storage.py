"""`core.storage` sans Garage (story 1.10) : contrôles, ré-encodage et hooks de transaction.

Les octets sont fabriqués avec Pillow (`tests/photos.py`). L'écriture S3 est remplacée
par un faux en mémoire pour tester la mécanique des hooks ; le comportement réel sur
Garage est couvert par `tests/integration/test_storage_garage.py`.
"""

import asyncio
import hashlib
import io
import re
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import pytest
from botocore.exceptions import ClientError
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import clock, db, storage
from app.core.enums import PhotoKind
from app.core.errors import DomainError, ErrorCode
from tests import photos


class Boom(Exception):
    pass


def _refusal(data: bytes) -> DomainError:
    with pytest.raises(DomainError) as exc_info:
        storage.reencode(data)
    return exc_info.value


# --- Détection du format par les octets ----------------------------------------------


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (photos.encoded("JPEG"), "JPEG"),
        (photos.encoded("PNG"), "PNG"),
        (photos.encoded("WEBP"), "WEBP"),
        (photos.encoded("GIF"), None),
        (photos.encoded("BMP"), None),
        (b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n", None),
        (b"ceci est un texte renomme en photo.jpg", None),
        (b"RIFF\x00\x00\x00\x00WAVEfmt ", None),
        (b"RIFF", None),
        (b"", None),
    ],
    ids=["jpeg", "png", "webp", "gif", "bmp", "pdf", "texte", "riff-wav", "riff-court", "vide"],
)
def test_detect_format_reads_the_signature(data: bytes, expected: str | None) -> None:
    assert storage.detect_format(data) == expected


def test_pillow_pixel_guard_is_set_to_the_limit() -> None:
    assert Image.MAX_IMAGE_PIXELS == storage.MAX_PHOTO_PIXELS == 12_000_000


# --- Contrôles, dans l'ordre ----------------------------------------------------------


@pytest.mark.parametrize(
    ("data", "code", "status"),
    [
        # Trop lourd, même sans signature reconnue : le poids est contrôlé d'abord.
        (b"x" * (storage.MAX_PHOTO_BYTES + 1), ErrorCode.PHOTO_TOO_LARGE, 413),
        (
            b"\xff\xd8\xff" + b"\x00" * storage.MAX_PHOTO_BYTES,
            ErrorCode.PHOTO_TOO_LARGE,
            413,
        ),
        # Format inconnu, même illisible : 415 avant tout décodage.
        (photos.encoded("GIF"), ErrorCode.UNSUPPORTED_MEDIA_TYPE, 415),
        (b"%PDF-1.7\n", ErrorCode.UNSUPPORTED_MEDIA_TYPE, 415),
        (b"pas une photo", ErrorCode.UNSUPPORTED_MEDIA_TYPE, 415),
        # Trop de pixels dans l'en-tête, IDAT illisible : refus sans décoder.
        (photos.png_header_only(5000, 5000), ErrorCode.PHOTO_TOO_MANY_PIXELS, 422),
        (photos.png_header_only(4000, 3001), ErrorCode.PHOTO_TOO_MANY_PIXELS, 422),
        # Exactement 12 000 000 pixels : l'en-tête passe, le décodage échoue.
        (photos.png_header_only(4000, 3000), ErrorCode.PHOTO_UNREADABLE, 422),
        (b"\xff\xd8\xff" + bytes(range(256)) * 8, ErrorCode.PHOTO_UNREADABLE, 422),
        (photos.encoded("JPEG")[:200], ErrorCode.PHOTO_UNREADABLE, 422),
        (b"RIFF\x10\x00\x00\x00WEBPVP8 garbage", ErrorCode.PHOTO_UNREADABLE, 422),
    ],
    ids=[
        "trop-lourd-texte",
        "trop-lourd-jpeg",
        "gif",
        "pdf",
        "texte",
        "png-5000x5000",
        "png-4000x3001",
        "png-12mpx-illisible",
        "jpeg-aleatoire",
        "jpeg-tronque",
        "webp-corrompu",
    ],
)
def test_checks_in_order(data: bytes, code: ErrorCode, status: int) -> None:
    error = _refusal(data)
    assert (error.code, error.http_status) == (code, status)


def test_exactly_the_byte_limit_is_accepted() -> None:
    data = photos.encoded("PNG")
    padded = data + b"\x00" * (storage.MAX_PHOTO_BYTES - len(data))
    assert len(padded) == storage.MAX_PHOTO_BYTES
    storage.reencode(padded)  # octets en fin de fichier ignorés par Pillow


def test_too_many_pixels_never_decodes(monkeypatch: pytest.MonkeyPatch) -> None:
    def load(self: Image.Image) -> None:
        raise AssertionError("décodage complet interdit")

    monkeypatch.setattr(Image.Image, "load", load)
    monkeypatch.setattr("PIL.ImageFile.ImageFile.load", load)
    assert _refusal(photos.png_header_only(4000, 3001)).code is ErrorCode.PHOTO_TOO_MANY_PIXELS


def test_pillow_format_must_match_the_signature(monkeypatch: pytest.MonkeyPatch) -> None:
    # Signature PNG, mais Pillow lirait un JPEG : refus en 415.
    monkeypatch.setattr(storage, "detect_format", lambda data: "PNG")
    real_open = Image.open
    monkeypatch.setattr(
        storage.Image, "open", lambda fp, formats=None: real_open(fp, formats=["JPEG"])
    )
    assert _refusal(photos.encoded("JPEG")).code is ErrorCode.UNSUPPORTED_MEDIA_TYPE


# --- Ré-encodage sans métadonnées -------------------------------------------------------


def test_reencode_strips_every_metadata_and_applies_the_orientation() -> None:
    received = photos.jpeg_with_metadata((400, 300))
    # Témoin : la photo reçue porte bien toutes les métadonnées.
    assert photos.CAMERA_MAKE.encode() in received and photos.XMP_MARKER in received
    body, width, height = storage.reencode(received)

    assert (width, height) == (300, 400)  # orientation 6 : rotation de 90°
    with Image.open(io.BytesIO(body)) as stored:
        assert stored.format == "JPEG" and stored.mode == "RGB"
        assert stored.size == (300, 400)
        assert len(stored.getexif()) == 0
        for key in ("exif", "icc_profile", "xmp", "comment"):
            assert key not in stored.info, key
    assert not set(photos.jpeg_markers(body)) & photos.METADATA_MARKERS
    for marker in (photos.CAMERA_MAKE.encode(), photos.XMP_MARKER, photos.COMMENT_MARKER):
        assert marker not in body


def test_reencode_uses_quality_85(monkeypatch: pytest.MonkeyPatch) -> None:
    saved: dict[str, Any] = {}
    real_save = Image.Image.save

    def save(self: Image.Image, fp: Any, format: str | None = None, **params: Any) -> None:
        saved.update(params, format=format)
        real_save(self, fp, format=format, **params)

    monkeypatch.setattr(Image.Image, "save", save)
    storage.reencode(photos.encoded("PNG"))
    assert saved["format"] == "JPEG" and saved["quality"] == 85
    assert not {"exif", "icc_profile", "xmp", "comment"} & saved.keys()


@pytest.mark.parametrize("data", [photos.png_transparent(), photos.png_palette_transparent()])
def test_transparency_becomes_white(data: bytes) -> None:
    body, width, height = storage.reencode(data)
    with Image.open(io.BytesIO(body)) as stored:
        assert stored.mode == "RGB" and stored.size == (width, height)
        # Coin opaque gardé, reste transparent → blanc (JPEG : à quelques unités près).
        corner = stored.getpixel((2, 2))
        background = stored.getpixel((width - 2, height - 2))
    assert isinstance(corner, tuple) and isinstance(background, tuple)
    assert min(background) >= 245, background
    assert max(corner) >= 200 and min(corner) <= 60, corner


@pytest.mark.parametrize("fmt", ["WEBP", "PNG", "JPEG"])
def test_every_accepted_format_is_stored_as_jpeg(fmt: str) -> None:
    body, width, height = storage.reencode(photos.encoded(fmt, (48, 32)))
    assert body.startswith(b"\xff\xd8\xff")
    assert (width, height) == (48, 32)


# --- ingest_photo / purge avec un faux S3 --------------------------------------------


class FakeBucket:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.deleted: list[str] = []

    def put(self, key: str, body: bytes) -> None:
        self.objects[key] = body

    def delete(self, key: str) -> None:
        self.deleted.append(key)
        self.objects.pop(key, None)


@pytest.fixture
def bucket(monkeypatch: pytest.MonkeyPatch) -> FakeBucket:
    fake = FakeBucket()
    monkeypatch.setattr(storage, "_put", fake.put)
    monkeypatch.setattr(storage, "_delete", fake.delete)
    return fake


@pytest.fixture
def uow(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    monkeypatch.setattr(
        db, "get_sessionmaker", lambda: sessionmaker(bind=engine, expire_on_commit=False)
    )
    yield
    engine.dispose()


@pytest.fixture
def fixed_clock(monkeypatch: pytest.MonkeyPatch) -> datetime:
    moment = datetime(2031, 2, 28, 23, 59, tzinfo=UTC)
    monkeypatch.setattr(clock, "now", lambda: moment)
    return moment


KEY = re.compile(
    r"(report|proof)/2031/02/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\.jpg"
)


def test_ingest_and_purge_refuse_to_run_outside_a_unit_of_work(bucket: FakeBucket) -> None:
    with pytest.raises(RuntimeError, match="unité de travail"):
        storage.ingest_photo(PhotoKind.REPORT, photos.encoded("JPEG"))
    with pytest.raises(RuntimeError, match="unité de travail"):
        storage.purge(["report/2031/02/x.jpg"])
    assert bucket.objects == {} and bucket.deleted == []


@pytest.mark.parametrize("kind", list(PhotoKind))
def test_ingest_stores_under_kind_year_month_uuid(
    bucket: FakeBucket, uow: None, fixed_clock: datetime, kind: PhotoKind
) -> None:
    received = photos.jpeg_with_metadata((400, 300))
    with db.unit_of_work():
        stored = storage.ingest_photo(kind, received)
    assert KEY.fullmatch(stored.object_key) and stored.object_key.startswith(f"{kind}/")
    assert stored.sha256 == hashlib.sha256(received).hexdigest()
    assert (stored.width, stored.height) == (300, 400)
    assert list(bucket.objects) == [stored.object_key]
    assert bucket.deleted == []


def test_two_photos_get_two_keys(bucket: FakeBucket, uow: None) -> None:
    with db.unit_of_work():
        first = storage.ingest_photo(PhotoKind.REPORT, photos.encoded("JPEG"))
        second = storage.ingest_photo(PhotoKind.REPORT, photos.encoded("JPEG"))
    assert first.object_key != second.object_key
    assert first.sha256 == second.sha256


def test_refused_photo_writes_nothing(bucket: FakeBucket, uow: None) -> None:
    with pytest.raises(DomainError), db.unit_of_work():
        storage.ingest_photo(PhotoKind.REPORT, photos.encoded("GIF"))
    assert bucket.objects == {} and bucket.deleted == []


def test_rollback_deletes_the_stored_object(bucket: FakeBucket, uow: None) -> None:
    with pytest.raises(Boom), db.unit_of_work():
        stored = storage.ingest_photo(PhotoKind.REPORT, photos.encoded("PNG"))
        assert list(bucket.objects) == [stored.object_key]
        raise Boom
    assert bucket.objects == {}
    assert bucket.deleted == [stored.object_key]


def test_failed_write_is_cleaned_up_on_rollback(
    bucket: FakeBucket, uow: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    def put(key: str, body: bytes) -> None:
        bucket.put(key, body)  # écrit, mais signalé en échec (délai dépassé)
        raise TimeoutError

    monkeypatch.setattr(storage, "_put", put)
    with pytest.raises(TimeoutError), db.unit_of_work():
        storage.ingest_photo(PhotoKind.REPORT, photos.encoded("PNG"))
    assert bucket.objects == {} and len(bucket.deleted) == 1


def test_purge_runs_after_commit_only(bucket: FakeBucket, uow: None) -> None:
    bucket.objects = {"a": b"1", "b": b"2"}
    with db.unit_of_work():
        storage.purge(["a"])
        assert bucket.deleted == []  # rien avant le commit
    assert bucket.objects == {"b": b"2"}

    with pytest.raises(Boom), db.unit_of_work():
        storage.purge(["b"])
        raise Boom
    assert bucket.objects == {"b": b"2"}


def test_purge_continues_after_a_failed_deletion(
    bucket: FakeBucket, uow: None, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    def delete(key: str) -> None:
        if key == "a":
            raise ConnectionError
        bucket.delete(key)

    monkeypatch.setattr(storage, "_delete", delete)
    bucket.objects = {"a": b"1", "b": b"2"}
    with db.unit_of_work():
        storage.purge(["a", "b"])
    assert bucket.objects == {"a": b"1"}
    out = capsys.readouterr().out
    assert '"event": "photo_purged_failed"' in out and '"object_key": "a"' in out


def test_purge_of_nothing_and_invalid_keys(bucket: FakeBucket, uow: None) -> None:
    with db.unit_of_work():
        storage.purge([])
        with pytest.raises(ValueError, match="Clé"):
            storage.purge([""])
    assert bucket.deleted == []


def test_async_unit_of_work_runs_s3_effects_off_the_event_loop(
    bucket: FakeBucket, uow: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    threads: list[bool] = []

    def delete(key: str) -> None:
        try:
            asyncio.get_running_loop()
            threads.append(False)  # dans la boucle asyncio : bloquant
        except RuntimeError:
            threads.append(True)
        bucket.delete(key)

    monkeypatch.setattr(storage, "_delete", delete)

    async def scenario() -> None:
        with pytest.raises(Boom):
            async with db.async_unit_of_work():
                storage.ingest_photo(PhotoKind.REPORT, photos.encoded("JPEG"))
                raise Boom
        async with db.async_unit_of_work():
            storage.purge(["x"])

    asyncio.run(scenario())
    assert threads == [True, True]
    assert bucket.objects == {}


def test_logs_carry_only_the_key(
    bucket: FakeBucket, uow: None, capsys: pytest.CaptureFixture
) -> None:
    received = photos.jpeg_with_metadata((40, 30))
    with db.unit_of_work():
        stored = storage.ingest_photo(PhotoKind.REPORT, received)
    lines = [line for line in capsys.readouterr().out.splitlines() if "photo_" in line]
    assert len(lines) == 1 and '"event": "photo_stored"' in lines[0]
    assert stored.object_key in lines[0]
    for forbidden in (stored.sha256, photos.CAMERA_MAKE, "width", "height", "sha256"):
        assert forbidden not in lines[0]


# --- Client S3 ---------------------------------------------------------------------


def test_delete_ignores_a_missing_object(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    class Client:
        def delete_object(self, Bucket: str, Key: str) -> None:  # noqa: N803 (API boto3)
            calls.append(Key)
            if Key == "missing":
                raise ClientError({"Error": {"Code": "NoSuchKey"}}, "DeleteObject")
            raise ClientError({"Error": {"Code": "AccessDenied"}}, "DeleteObject")

    monkeypatch.setattr(storage, "_client_and_bucket", lambda: (Client(), "bucket"))
    storage._delete("missing")
    with pytest.raises(ClientError):
        storage._delete("forbidden")
    assert calls == ["missing", "forbidden"]


def test_storage_client_is_dedicated_and_configured_for_garage() -> None:
    from app.core import health

    storage._s3_client.cache_clear()
    try:
        client = storage._s3_client("http://garage:3900", "garage", "AK", "SK")
        config = client.meta.config
        assert config.s3["addressing_style"] == "path"
        assert config.signature_version == "s3v4"
        assert config.request_checksum_calculation == "when_required"
        assert config.connect_timeout == storage.S3_CONNECT_TIMEOUT_S
        assert config.read_timeout == storage.S3_READ_TIMEOUT_S
        assert config.retries["total_max_attempts"] == storage.S3_MAX_ATTEMPTS > 1
        assert client is not health._s3_client("http://garage:3900", "garage", "AK", "SK")
    finally:
        storage._s3_client.cache_clear()
        health._s3_client.cache_clear()


def test_missing_credentials_is_a_configuration_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class Settings:
        s3_access_key_id = None
        s3_secret_access_key = None

    monkeypatch.setattr(storage, "get_settings", lambda: Settings())
    with pytest.raises(RuntimeError, match="identifiants S3"):
        storage._client_and_bucket()
