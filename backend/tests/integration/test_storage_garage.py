"""`core.storage` sur Garage réel (story 1.10) : objet relu sans métadonnées, nettoyage
au rollback, purge après commit seulement, bucket privé.

Exige la pile démarrée et les variables `TEST_S3_ENDPOINT` (API S3 publiée sur l'hôte),
`TEST_S3_BUCKET`, `TEST_S3_ACCESS_KEY_ID` et `TEST_S3_SECRET_ACCESS_KEY`. Sans elles,
les tests sont ignorés, sauf avec `REQUIRE_INTEGRATION=1` (CI) : ils échouent alors.

L'unité de travail tourne sur un SQLite en mémoire : seule sa mécanique
(`after_commit`, `after_rollback`) compte ici, pas la base.
"""

import io
import os
import urllib.error
import urllib.request
import uuid
from collections.abc import Iterator
from typing import Any

import pytest
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import db, storage
from app.core.config import get_settings
from app.core.db import unit_of_work
from app.core.enums import PhotoKind
from app.core.errors import DomainError
from tests.photos import has_metadata, jpeg_with_exif_and_gps

pytestmark = pytest.mark.integration

_VARS = {
    "S3_ENDPOINT": "TEST_S3_ENDPOINT",
    "S3_BUCKET": "TEST_S3_BUCKET",
    "S3_ACCESS_KEY_ID": "TEST_S3_ACCESS_KEY_ID",
    "S3_SECRET_ACCESS_KEY": "TEST_S3_SECRET_ACCESS_KEY",
}


class Boom(Exception):
    pass


@pytest.fixture
def garage(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[Any, str]]:
    """Réglages pointés sur le Garage de la pile ; renvoie (client S3, bucket)."""
    for setting, var in _VARS.items():
        value = os.environ.get(var)
        if not value:
            pytest.skip(f"{var} non défini : tests d'intégration ignorés")
        monkeypatch.setenv(setting, value)
    get_settings.cache_clear()
    storage._s3_client.cache_clear()
    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    monkeypatch.setattr(
        db, "get_sessionmaker", lambda: sessionmaker(bind=engine, expire_on_commit=False)
    )
    try:
        yield storage._client_and_bucket()
    finally:
        engine.dispose()
        get_settings.cache_clear()
        storage._s3_client.cache_clear()


def _count(client: Any, bucket: str) -> int:
    pages = client.get_paginator("list_objects_v2").paginate(Bucket=bucket)
    return sum(page.get("KeyCount", 0) for page in pages)


def _exists(client: Any, bucket: str, key: str) -> bool:
    response = client.list_objects_v2(Bucket=bucket, Prefix=key)
    return any(item["Key"] == key for item in response.get("Contents", []))


def _read(client: Any, bucket: str, key: str) -> bytes:
    return client.get_object(Bucket=bucket, Key=key)["Body"].read()


def test_stored_object_has_no_metadata(garage: tuple[Any, str]) -> None:
    client, bucket = garage
    with unit_of_work():
        stored = storage.ingest_photo(PhotoKind.REPORT, jpeg_with_exif_and_gps())
    try:
        body = _read(client, bucket, stored.object_key)
        assert not has_metadata(body)
        with Image.open(io.BytesIO(body)) as reread:
            assert reread.format == "JPEG"
            assert reread.size == (stored.width, stored.height) == (60, 80)
        head = client.head_object(Bucket=bucket, Key=stored.object_key)
        assert head["ContentType"] == "image/jpeg"
    finally:
        client.delete_object(Bucket=bucket, Key=stored.object_key)


def test_anonymous_read_is_refused(garage: tuple[Any, str]) -> None:
    client, bucket = garage
    with unit_of_work():
        stored = storage.ingest_photo(PhotoKind.REPORT, jpeg_with_exif_and_gps())
    try:
        url = f"{os.environ['TEST_S3_ENDPOINT'].rstrip('/')}/{bucket}/{stored.object_key}"
        with pytest.raises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(url, timeout=5)  # noqa: S310 - URL du Garage de test
        assert caught.value.code == 403
    finally:
        client.delete_object(Bucket=bucket, Key=stored.object_key)


def test_rollback_leaves_no_object(garage: tuple[Any, str]) -> None:
    client, bucket = garage
    before = _count(client, bucket)
    key = None
    with pytest.raises(Boom), unit_of_work():
        key = storage.ingest_photo(PhotoKind.REPORT, jpeg_with_exif_and_gps()).object_key
        assert _exists(client, bucket, key)  # écrit avant le commit
        raise Boom
    assert key is not None
    assert not _exists(client, bucket, key)
    assert _count(client, bucket) == before


@pytest.mark.parametrize(
    "data",
    [b"\x00" * 1_000_001, b"pas une photo", b"\xff\xd8\xff\xe0tronque"],
    ids=["trop-lourd", "faux-type", "illisible"],
)
def test_refused_photo_leaves_no_object(garage: tuple[Any, str], data: bytes) -> None:
    client, bucket = garage
    before = _count(client, bucket)
    with pytest.raises(DomainError), unit_of_work():
        storage.ingest_photo(PhotoKind.REPORT, data)
    assert _count(client, bucket) == before


def test_purge_deletes_only_after_commit(garage: tuple[Any, str]) -> None:
    client, bucket = garage
    with unit_of_work():
        key = storage.ingest_photo(PhotoKind.BEFORE, jpeg_with_exif_and_gps()).object_key
    try:
        with pytest.raises(Boom), unit_of_work():
            storage.purge([key])
            raise Boom
        assert _exists(client, bucket, key)  # rollback : rien de supprimé

        with unit_of_work():
            storage.purge([key])
            assert _exists(client, bucket, key)  # pas encore commité
        assert not _exists(client, bucket, key)
    finally:
        client.delete_object(Bucket=bucket, Key=key)


def test_purge_of_missing_object_is_not_an_error(
    garage: tuple[Any, str], capsys: pytest.CaptureFixture[str]
) -> None:
    with unit_of_work():
        storage.purge([f"report/2000/01/{uuid.uuid4()}.jpg"])
    assert "storage_delete_failed" not in capsys.readouterr().out
