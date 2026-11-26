"""Miniature d'une photo de Signalement sans Garage (story 1.18) : clé dérivée, plafond de
30 Kio, pas d'agrandissement, aucune métadonnée, erreurs de lecture et d'écriture.

Les photos sont fabriquées avec Pillow (`tests/photos.py`) puis nettoyées par
`storage.reencode`, comme celles que stocke `ingest_photo` : la miniature part toujours de
l'objet stocké. Lecture et écriture S3 remplacées par un faux en mémoire ; le comportement
réel sur Garage est couvert par `tests/integration/test_thumbnails.py`.
"""

import io

import pytest
from botocore.exceptions import ClientError
from PIL import Image

from app.core import storage
from app.core.errors import DomainError, ErrorCode
from tests import photos

UUID_A = "00000000-0000-4000-8000-00000000000a"
REPORT_KEY = f"report/2026/11/{UUID_A}.jpg"
THUMB_KEY = f"report_thumb/2026/11/{UUID_A}.jpg"

# Dix photos d'environ 1 Mo à forte entropie, de proportions variées.
ASPECTS = [(4, 3), (3, 4), (16, 9), (9, 16), (1, 1), (3, 1), (1, 3), (5, 4), (2, 1), (21, 9)]


def _stored(data: bytes) -> bytes:
    """Objet tel que `ingest_photo` le stocke (contrôlé, ré-encodé sans métadonnée)."""
    body, _, _ = storage.reencode(data)
    return body


def _assert_clean_jpeg(body: bytes) -> Image.Image:
    assert not set(photos.jpeg_markers(body)) & photos.METADATA_MARKERS
    image = Image.open(io.BytesIO(body))
    assert image.format == "JPEG"
    assert not image.getexif()
    for key in ("exif", "icc_profile", "xmp", "comment"):
        assert key not in image.info
    return image


# --- Clé dérivée ---------------------------------------------------------------------


def test_thumb_key_keeps_year_month_and_uuid() -> None:
    assert storage.thumb_key_for(REPORT_KEY) == THUMB_KEY
    assert storage.thumb_key_for(f"report/2032/05/{UUID_A}.jpg") == (
        f"report_thumb/2032/05/{UUID_A}.jpg"
    )


@pytest.mark.parametrize(
    "key",
    [
        "",
        f"proof/2026/11/{UUID_A}.jpg",
        THUMB_KEY,
        f"report/26/11/{UUID_A}.jpg",
        f"report/2026/11/{UUID_A}.png",
        f"../report/2026/11/{UUID_A}.jpg",
        f"xreport/2026/11/{UUID_A}.jpg",
        f"{REPORT_KEY}/x",
        None,
    ],
)
def test_thumb_key_refuses_anything_but_a_report_photo_key(key: object) -> None:
    with pytest.raises(ValueError, match="Clé"):
        storage.thumb_key_for(key)  # type: ignore[arg-type]


# --- Rendu ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("aspect", "seed"), [(aspect, seed) for seed, aspect in enumerate(ASPECTS)]
)
def test_ten_high_entropy_1_mb_photos_fit_under_the_cap(aspect: tuple[int, int], seed: int) -> None:
    received = photos.high_entropy_jpeg(aspect, seed)
    assert 900_000 <= len(received) <= storage.MAX_PHOTO_BYTES
    body, width, height = storage.render_thumbnail(_stored(received))
    assert len(body) <= storage.MAX_THUMB_BYTES == 30_720
    assert max(width, height) <= storage.THUMB_MAX_SIDE == 320
    image = _assert_clean_jpeg(body)
    assert image.size == (width, height)
    # Proportions gardées (à l'arrondi près).
    assert width / height == pytest.approx(aspect[0] / aspect[1], rel=0.05)


def test_small_photo_is_never_enlarged() -> None:
    body, width, height = storage.render_thumbnail(_stored(photos.encoded("JPEG", (64, 48))))
    assert (width, height) == (64, 48)
    assert _assert_clean_jpeg(body).size == (64, 48)


def test_large_photo_is_reduced_to_320_on_its_longest_side() -> None:
    _, width, height = storage.render_thumbnail(_stored(photos.encoded("JPEG", (4000, 3000))))
    assert (width, height) == (320, 240)


def test_no_metadata_even_from_a_source_that_has_some() -> None:
    """Défense en profondeur : même une source portant EXIF, GPS, ICC, XMP et commentaire
    (jamais stockée ainsi) donne une miniature sans aucune métadonnée."""
    body, _, _ = storage.render_thumbnail(photos.jpeg_with_metadata((400, 300)))
    _assert_clean_jpeg(body)
    for marker in (photos.CAMERA_MAKE.encode(), photos.XMP_MARKER, photos.COMMENT_MARKER):
        assert marker not in body


def test_qualities_are_tried_in_order_then_sides_shrink(monkeypatch: pytest.MonkeyPatch) -> None:
    """Plafond abaissé : 75, 65, 55, 45 et 35 ne suffisent pas, les côtés sont réduits de
    25 % jusqu'à tenir ; le plafond reste garanti par construction."""
    calls: list[tuple[int, tuple[int, int]]] = []
    real_jpeg = storage._jpeg

    def recording(image: Image.Image, quality: int) -> bytes:
        calls.append((quality, image.size))
        return real_jpeg(image, quality)

    monkeypatch.setattr(storage, "_jpeg", recording)
    monkeypatch.setattr(storage, "MAX_THUMB_BYTES", 4_000)
    source = _stored(photos.high_entropy_jpeg((4, 3), seed=42))
    body, width, height = storage.render_thumbnail(source)

    assert len(body) <= 4_000
    assert [quality for quality, _ in calls[:5]] == [75, 65, 55, 45, 35]
    assert {size for _, size in calls[:5]} == {(320, 240)}
    sizes = list(dict.fromkeys(size for _, size in calls))
    assert sizes[:2] == [(320, 240), (240, 180)]
    assert sizes[-1] == (width, height)


def test_simple_photo_keeps_the_first_quality(monkeypatch: pytest.MonkeyPatch) -> None:
    qualities: list[int] = []
    real_jpeg = storage._jpeg

    def recording(image: Image.Image, quality: int) -> bytes:
        qualities.append(quality)
        return real_jpeg(image, quality)

    monkeypatch.setattr(storage, "_jpeg", recording)
    storage.render_thumbnail(_stored(photos.encoded("JPEG", (800, 600))))
    assert qualities == [75]


@pytest.mark.parametrize(
    "data",
    [b"", b"\xff\xd8\xff" + b"\x00" * 64, photos.encoded("PNG"), b"pas une image"],
)
def test_unreadable_source_is_a_source_error(data: bytes) -> None:
    with pytest.raises(storage.ThumbnailSourceError):
        storage.render_thumbnail(data)


# --- Lecture et écriture ---------------------------------------------------------------


class FakeBucket:
    def __init__(self, objects: dict[str, bytes] | None = None) -> None:
        self.objects = dict(objects or {})
        self.puts: list[str] = []

    def get(self, key: str) -> bytes:
        if key not in self.objects:
            raise ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")
        return self.objects[key]

    def put(self, key: str, body: bytes) -> None:
        self.puts.append(key)
        self.objects[key] = body


@pytest.fixture
def bucket(monkeypatch: pytest.MonkeyPatch) -> FakeBucket:
    fake = FakeBucket({REPORT_KEY: _stored(photos.encoded("JPEG", (800, 600)))})
    monkeypatch.setattr(storage, "_get", fake.get)
    monkeypatch.setattr(storage, "_put", fake.put)
    return fake


def test_make_thumbnail_stores_under_the_derived_key(
    bucket: FakeBucket, capsys: pytest.CaptureFixture[str]
) -> None:
    capsys.readouterr()
    assert storage.make_thumbnail(REPORT_KEY) == THUMB_KEY
    assert bucket.puts == [THUMB_KEY]
    assert len(bucket.objects[THUMB_KEY]) <= storage.MAX_THUMB_BYTES
    # Rejouer réécrit le même objet.
    assert storage.make_thumbnail(REPORT_KEY) == THUMB_KEY
    assert bucket.puts == [THUMB_KEY, THUMB_KEY]
    assert set(bucket.objects) == {REPORT_KEY, THUMB_KEY}
    out = capsys.readouterr().out
    assert '"thumb_stored"' in out and "width" not in out


def test_missing_source_is_a_source_error(bucket: FakeBucket) -> None:
    bucket.objects.clear()
    with pytest.raises(storage.ThumbnailSourceError):
        storage.make_thumbnail(REPORT_KEY)
    assert bucket.puts == []


def test_corrupt_source_is_a_source_error(bucket: FakeBucket) -> None:
    bucket.objects[REPORT_KEY] = b"\xff\xd8\xff" + b"\x00" * 64
    with pytest.raises(storage.ThumbnailSourceError):
        storage.make_thumbnail(REPORT_KEY)
    assert bucket.puts == []


@pytest.mark.parametrize(
    "error",
    [
        ClientError({"Error": {"Code": "InternalError"}}, "GetObject"),
        ConnectionError("garage indisponible"),
    ],
)
def test_unreadable_storage_is_503(
    monkeypatch: pytest.MonkeyPatch, bucket: FakeBucket, error: Exception
) -> None:
    def failing(key: str) -> bytes:
        raise error

    monkeypatch.setattr(storage, "_get", failing)
    with pytest.raises(DomainError) as exc_info:
        storage.make_thumbnail(REPORT_KEY)
    assert (exc_info.value.code, exc_info.value.http_status) == (
        ErrorCode.STORAGE_UNAVAILABLE,
        503,
    )
    assert bucket.puts == []


def test_failed_write_is_503(monkeypatch: pytest.MonkeyPatch, bucket: FakeBucket) -> None:
    def failing(key: str, body: bytes) -> None:
        raise ConnectionError("garage indisponible")

    monkeypatch.setattr(storage, "_put", failing)
    with pytest.raises(DomainError) as exc_info:
        storage.make_thumbnail(REPORT_KEY)
    assert exc_info.value.code is ErrorCode.STORAGE_UNAVAILABLE


def test_make_thumbnail_refuses_a_key_that_is_not_a_report_photo(bucket: FakeBucket) -> None:
    with pytest.raises(ValueError, match="Clé"):
        storage.make_thumbnail(f"proof/2026/11/{UUID_A}.jpg")
    assert bucket.puts == []


def test_get_reads_and_closes_the_body(monkeypatch: pytest.MonkeyPatch) -> None:
    closed: list[bool] = []

    class Body(io.BytesIO):
        def close(self) -> None:
            closed.append(True)
            super().close()

    class Client:
        def get_object(self, Bucket: str, Key: str) -> dict:  # noqa: N803 (API boto3)
            assert (Bucket, Key) == ("bucket", REPORT_KEY)
            return {"Body": Body(b"octets")}

    monkeypatch.setattr(storage, "_client_and_bucket", lambda: (Client(), "bucket"))
    assert storage._get(REPORT_KEY) == b"octets"
    assert closed == [True]
