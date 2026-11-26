"""`core.storage` sans S3 (story 1.10) : contrôles des octets, ré-encodage sans
métadonnées, forme de la clé, et appels au client S3 selon l'issue de l'unité de travail.

Le client S3 est remplacé par un faux qui enregistre les appels ; l'unité de travail
tourne sur un SQLite en mémoire (mécanique seulement). Le comportement sur Garage réel
est vérifié par `tests/integration/test_storage_garage.py`.
"""

import asyncio
import hashlib
import io
import threading
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import pytest
from botocore.exceptions import ClientError
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import db, storage
from app.core.db import async_unit_of_work, unit_of_work
from app.core.enums import PhotoKind
from app.core.errors import DomainError
from tests.photos import encode, has_metadata, jpeg_with_exif_and_gps, noise

# Entre 12 et 24 Mpx, Pillow avertit avant le refus explicite de `_decode` : attendu.
pytestmark = pytest.mark.filterwarnings("ignore::PIL.Image.DecompressionBombWarning")


class Boom(Exception):
    pass


class FakeS3:
    """Client S3 factice : garde les objets en mémoire et note chaque appel."""

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.calls: list[tuple[str, str]] = []
        self.missing_error: str | None = None

    def put_object(self, *, Bucket: str, Key: str, Body: bytes, ContentType: str) -> dict:
        assert ContentType in ("image/jpeg", "audio/ogg", "audio/webm", "audio/mp4")
        self.calls.append(("put", Key))
        self.objects[Key] = Body
        return {}

    def delete_object(self, *, Bucket: str, Key: str) -> dict:
        self.calls.append(("delete", Key))
        if Key not in self.objects and self.missing_error:
            raise ClientError({"Error": {"Code": self.missing_error}}, "DeleteObject")
        self.objects.pop(Key, None)
        return {}


@pytest.fixture
def s3(monkeypatch: pytest.MonkeyPatch) -> FakeS3:
    fake = FakeS3()
    monkeypatch.setattr(storage, "_client_and_bucket", lambda: (fake, "bucket-test"))
    return fake


@pytest.fixture
def uow_db(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    monkeypatch.setattr(
        db, "get_sessionmaker", lambda: sessionmaker(bind=engine, expire_on_commit=False)
    )
    yield
    engine.dispose()


@pytest.fixture
def frozen_now(monkeypatch: pytest.MonkeyPatch) -> datetime:
    instant = datetime(2026, 11, 30, 23, 59, tzinfo=UTC)
    monkeypatch.setattr(storage, "now", lambda: instant)
    return instant


def _reject(data: bytes) -> DomainError:
    with pytest.raises(DomainError) as caught:
        storage.sanitize_photo(data)
    return caught.value


# --- Contrôles (matrice) ------------------------------------------------------------


def test_pillow_bomb_guard_is_set_explicitly() -> None:
    assert Image.MAX_IMAGE_PIXELS == 12_000_000


def test_photo_over_one_megabyte_is_413() -> None:
    error = _reject(b"\xff\xd8\xff" + b"\x00" * (1_000_001 - 3))
    assert (error.http_status, error.code.value) == (413, "photo_too_large")


def test_exactly_one_megabyte_passes_size_check() -> None:
    # 1 000 000 octets : pas refusé pour le poids (ici illisible, donc 422).
    error = _reject(b"\xff\xd8\xff" + b"\x00" * (1_000_000 - 3))
    assert error.code.value == "photo_unreadable"


@pytest.mark.parametrize(
    "data",
    [
        encode(noise(10, 10), "GIF"),
        b"%PDF-1.7\n1 0 obj\n<<>>\nendobj\n",
        b"je ne suis pas une photo.jpg",
        b"",
        b"RIFF\x00\x00\x00\x00WAVEfmt ",
    ],
    ids=["gif", "pdf", "texte", "vide", "riff-wave"],
)
def test_unsupported_type_is_415(data: bytes) -> None:
    error = _reject(data)
    assert (error.http_status, error.code.value) == (415, "unsupported_media_type")


def test_too_many_pixels_is_422_before_decoding() -> None:
    # 4000 × 3001 = 12 004 000 pixels, PNG uni : bien moins de 1 Mo.
    data = encode(Image.new("RGB", (4000, 3001), (10, 120, 60)), "PNG")
    assert len(data) <= 1_000_000
    error = _reject(data)
    assert (error.http_status, error.code.value) == (422, "photo_too_many_pixels")


def test_huge_pixel_count_hits_pillow_hard_limit_as_too_many_pixels() -> None:
    # 5000 × 5000 = 25 Mpx : au-delà du double du plafond, Pillow refuse dès l'ouverture.
    data = encode(Image.new("RGB", (5000, 5000)), "PNG")
    assert len(data) <= 1_000_000
    error = _reject(data)
    assert (error.http_status, error.code.value) == (422, "photo_too_many_pixels")


def test_exactly_twelve_megapixels_is_accepted() -> None:
    data = encode(Image.new("RGB", (4000, 3000), (10, 120, 60)), "PNG")
    _, width, height = storage.sanitize_photo(data)
    assert (width, height) == (4000, 3000)


@pytest.mark.parametrize(
    "fmt", ["JPEG", "PNG", "WEBP"], ids=["jpeg-tronque", "png-tronque", "webp-tronque"]
)
def test_truncated_image_is_422_unreadable(fmt: str) -> None:
    data = encode(noise(200, 150), fmt)
    error = _reject(data[: len(data) // 2])
    assert (error.http_status, error.code.value) == (422, "photo_unreadable")


def test_garbage_after_valid_signature_is_unreadable() -> None:
    error = _reject(b"\x89PNG\r\n\x1a\n" + b"\x13" * 500)
    assert error.code.value == "photo_unreadable"


def test_error_messages_never_contain_photo_bytes() -> None:
    error = _reject(b"secret-octets-de-photo")
    assert "secret" not in error.message


# --- Ré-encodage --------------------------------------------------------------------


def test_jpeg_metadata_is_removed_and_orientation_applied() -> None:
    original = jpeg_with_exif_and_gps(width=80, height=60)
    assert has_metadata(original)  # le cas de test porte bien des métadonnées
    jpeg, width, height = storage.sanitize_photo(original)
    assert (width, height) == (60, 80)  # orientation 6 : image tournée
    assert not has_metadata(jpeg)
    with Image.open(io.BytesIO(jpeg)) as reread:
        assert reread.format == "JPEG"
        assert reread.size == (60, 80)
        assert not reread.getexif()


def test_transparent_png_becomes_rgb_on_white() -> None:
    image = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
    jpeg, *_ = storage.sanitize_photo(encode(image, "PNG"))
    with Image.open(io.BytesIO(jpeg)) as reread:
        assert reread.mode == "RGB"
        red, green, blue = reread.getpixel((10, 10))
        assert min(red, green, blue) > 240


@pytest.mark.parametrize("mode", ["RGB", "RGBA"])
def test_webp_is_accepted(mode: str) -> None:
    jpeg, width, height = storage.sanitize_photo(encode(noise(32, 24, mode), "WEBP"))
    assert (width, height) == (32, 24)
    assert jpeg[:3] == b"\xff\xd8\xff"
    assert not has_metadata(jpeg)


@pytest.mark.parametrize(
    ("image", "transparency"),
    [
        (Image.new("P", (8, 8), 0), 0),
        (Image.new("RGB", (8, 8), (0, 0, 0)), (0, 0, 0)),
        (Image.new("L", (8, 8), 0), 0),
    ],
    ids=["palette", "rgb-trns", "gris-trns"],
)
def test_transparent_colour_key_becomes_white(image: Image.Image, transparency: object) -> None:
    if image.mode == "P":
        image.putpalette([0, 0, 0] * 256)
    jpeg, *_ = storage.sanitize_photo(encode(image, "PNG", transparency=transparency))
    with Image.open(io.BytesIO(jpeg)) as reread:
        assert min(reread.getpixel((4, 4))) > 240


def test_grayscale_and_palette_png_become_rgb() -> None:
    for image in (noise(16, 16, "L"), noise(16, 16).convert("P")):
        jpeg, *_ = storage.sanitize_photo(encode(image, "PNG"))
        with Image.open(io.BytesIO(jpeg)) as reread:
            assert reread.mode == "RGB"


def test_extension_and_content_type_are_ignored() -> None:
    # Le format vient des octets : un PNG est reconnu comme tel, quel que soit son nom.
    assert storage.sniff_format(encode(noise(4, 4), "PNG")) == "PNG"
    assert storage.sniff_format(encode(noise(4, 4), "JPEG")) == "JPEG"


# --- Clé et unité de travail ----------------------------------------------------------


def test_object_key_uses_utc_month_and_photo_id(frozen_now: datetime) -> None:
    photo_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
    assert storage.object_key(PhotoKind.REPORT, photo_id) == (
        "report/2026/11/12345678-1234-5678-1234-567812345678.jpg"
    )
    assert storage.object_key(PhotoKind.BEFORE, photo_id).startswith("before/2026/11/")


def test_ingest_outside_unit_of_work_is_refused(s3: FakeS3) -> None:
    with pytest.raises(RuntimeError):
        storage.ingest_photo(PhotoKind.REPORT, jpeg_with_exif_and_gps())
    assert s3.calls == []


def test_ingest_stores_clean_jpeg_and_returns_received_sha256(
    s3: FakeS3, uow_db: None, frozen_now: datetime
) -> None:
    original = jpeg_with_exif_and_gps()
    photo_id = uuid.uuid4()
    with unit_of_work():
        stored = storage.ingest_photo("report", original, photo_id=photo_id)
    assert stored.photo_id == photo_id
    assert stored.object_key == f"report/2026/11/{photo_id}.jpg"
    assert stored.sha256 == hashlib.sha256(original).hexdigest()
    assert (stored.width, stored.height) == (60, 80)
    assert s3.calls == [("put", stored.object_key)]
    assert not has_metadata(s3.objects[stored.object_key])


def test_ingest_generates_photo_id_when_missing(s3: FakeS3, uow_db: None) -> None:
    with unit_of_work():
        stored = storage.ingest_photo(PhotoKind.LOT, jpeg_with_exif_and_gps())
    assert stored.object_key.endswith(f"/{stored.photo_id}.jpg")
    assert stored.object_key.startswith("lot/")


def test_unknown_kind_is_refused(s3: FakeS3, uow_db: None) -> None:
    with unit_of_work(), pytest.raises(ValueError):
        storage.ingest_photo("selfie", jpeg_with_exif_and_gps())
    assert s3.calls == []


@pytest.mark.parametrize(
    "data",
    [b"\x00" * 1_000_001, b"texte", encode(Image.new("RGB", (4000, 3001)), "PNG")],
    ids=["trop-lourd", "faux-type", "trop-de-pixels"],
)
def test_refused_photo_never_reaches_storage(s3: FakeS3, uow_db: None, data: bytes) -> None:
    with pytest.raises(DomainError), unit_of_work():
        storage.ingest_photo(PhotoKind.REPORT, data)
    assert s3.calls == []
    assert s3.objects == {}


def test_rollback_deletes_stored_object(s3: FakeS3, uow_db: None) -> None:
    with pytest.raises(Boom), unit_of_work():
        stored = storage.ingest_photo(PhotoKind.REPORT, jpeg_with_exif_and_gps())
        raise Boom
    assert s3.calls == [("put", stored.object_key), ("delete", stored.object_key)]
    assert s3.objects == {}


def test_failed_put_is_cleaned_up_on_rollback(
    s3: FakeS3, uow_db: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    def failing_put(**kwargs: Any) -> dict:
        s3.calls.append(("put", kwargs["Key"]))
        raise ConnectionError

    monkeypatch.setattr(s3, "put_object", failing_put)
    with pytest.raises(ConnectionError), unit_of_work():
        storage.ingest_photo(PhotoKind.REPORT, jpeg_with_exif_and_gps())
    assert [call[0] for call in s3.calls] == ["put", "delete"]


def test_purge_waits_for_commit(s3: FakeS3, uow_db: None) -> None:
    s3.objects = {"report/2026/11/a.jpg": b"x", "report/2026/11/b.jpg": b"y"}
    with unit_of_work():
        storage.purge(["report/2026/11/a.jpg", "report/2026/11/b.jpg"])
        assert s3.calls == []  # rien avant le commit
    assert s3.objects == {}


def test_purge_does_nothing_on_rollback(s3: FakeS3, uow_db: None) -> None:
    s3.objects = {"report/2026/11/a.jpg": b"x"}
    with pytest.raises(Boom), unit_of_work():
        storage.purge(["report/2026/11/a.jpg"])
        raise Boom
    assert s3.calls == []
    assert "report/2026/11/a.jpg" in s3.objects


@pytest.mark.parametrize("error_code", [None, "NoSuchKey", "404"])
def test_purge_of_missing_object_is_not_an_error(
    s3: FakeS3, uow_db: None, capsys: pytest.CaptureFixture[str], error_code: str | None
) -> None:
    s3.missing_error = error_code
    with unit_of_work():
        storage.purge(["report/2026/11/absent.jpg"])
    assert s3.calls == [("delete", "report/2026/11/absent.jpg")]
    assert "storage_delete_failed" not in capsys.readouterr().out


def test_delete_failure_is_logged_without_key(
    s3: FakeS3, uow_db: None, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    def failing_delete(**kwargs: Any) -> dict:
        raise ClientError({"Error": {"Code": "AccessDenied"}}, "DeleteObject")

    monkeypatch.setattr(s3, "delete_object", failing_delete)
    with unit_of_work():
        storage.purge(["report/2026/11/cle-secrete.jpg"])
    out = capsys.readouterr().out
    assert "storage_delete_failed" in out
    assert "cle-secrete" not in out


def test_purge_refuses_a_single_key_string(s3: FakeS3, uow_db: None) -> None:
    with unit_of_work(), pytest.raises(TypeError):
        storage.purge("report/2026/11/a.jpg")


def test_async_unit_of_work_runs_s3_calls_off_the_event_loop(
    s3: FakeS3, uow_db: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    threads: list[int] = []
    real_delete = s3.delete_object

    def recording_delete(**kwargs: Any) -> dict:
        threads.append(threading.get_ident())
        return real_delete(**kwargs)

    monkeypatch.setattr(s3, "delete_object", recording_delete)

    async def scenario() -> tuple[int, str]:
        loop_thread = threading.get_ident()
        with pytest.raises(Boom):
            async with async_unit_of_work():
                key = storage.ingest_photo(PhotoKind.REPORT, jpeg_with_exif_and_gps()).object_key
                raise Boom
        async with async_unit_of_work():
            storage.purge(["report/2026/11/autre.jpg"])
        return loop_thread, key

    loop_thread, key = asyncio.run(scenario())
    assert key not in s3.objects  # rollback : objet supprimé
    assert len(threads) == 2
    assert loop_thread not in threads  # jamais d'appel S3 bloquant sur la boucle


def test_purge_outside_unit_of_work_is_refused(s3: FakeS3) -> None:
    with pytest.raises(RuntimeError):
        storage.purge(["report/2026/11/a.jpg"])


def test_missing_credentials_refuse_client(monkeypatch: pytest.MonkeyPatch) -> None:
    class NoCreds:
        s3_access_key_id = None
        s3_secret_access_key = None

    monkeypatch.setattr(storage, "get_settings", lambda: NoCreds())
    with pytest.raises(RuntimeError):
        storage._client_and_bucket()


def test_s3_client_is_configured_for_garage() -> None:
    storage._s3_client.cache_clear()
    try:
        client = storage._s3_client("http://garage:3900", "garage", "AK", "SK")
        config = client.meta.config
        assert config.signature_version == "s3v4"
        assert config.s3["addressing_style"] == "path"
        assert config.request_checksum_calculation == "when_required"
        assert config.response_checksum_validation == "when_required"
        assert client.meta.region_name == "garage"
        assert (config.connect_timeout, config.read_timeout) == (3, 10)
        assert config.retries["total_max_attempts"] == 3
    finally:
        storage._s3_client.cache_clear()


# --- Note vocale -----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (b"\x1a\x45\xdf\xa3" + b"\x00" * 8, ("webm", "audio/webm")),
        (b"OggS" + b"\x00" * 8, ("ogg", "audio/ogg")),
        (b"\x00\x00\x00\x18ftypM4A " + b"\x00" * 8, ("m4a", "audio/mp4")),
        (b"RIFF\x00\x00\x00\x00WAVEfmt ", None),
        (b"", None),
    ],
    ids=["webm", "ogg", "mp4", "wav", "vide"],
)
def test_sniff_voice(data: bytes, expected: tuple[str, str] | None) -> None:
    assert storage.sniff_voice(data) == expected


def test_voice_checks_happen_before_storage(s3: FakeS3, uow_db: None) -> None:
    with pytest.raises(DomainError) as too_large, unit_of_work():
        storage.ingest_voice(b"OggS" + b"\x00" * 600_000)
    assert (too_large.value.http_status, too_large.value.code.value) == (413, "voice_too_large")
    with pytest.raises(DomainError) as wrong_type, unit_of_work():
        storage.ingest_voice(b"pas un son")
    assert wrong_type.value.http_status == 415
    assert s3.calls == []


def test_voice_is_stored_and_removed_on_rollback(
    s3: FakeS3, uow_db: None, frozen_now: datetime
) -> None:
    voice_id = uuid.uuid4()
    with pytest.raises(Boom), unit_of_work():
        stored = storage.ingest_voice(b"OggS" + b"\x00" * 100, voice_id)
        assert stored.object_key == f"voice/2026/11/{voice_id}.ogg"
        assert stored.content_type == "audio/ogg"
        raise Boom
    assert [call[0] for call in s3.calls] == ["put", "delete"]
