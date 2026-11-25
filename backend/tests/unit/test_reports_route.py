"""`POST /v1/reports` sans base (story 1.11) : principal, puis `meta` et photo.

Ces refus ont lieu avant le service : la base n'est pas configurée ici, et tout appel au
service répondrait 500. Le parcours complet (consentement, Zone, photo, écriture) est
vérifié sur la pile réelle par `tests/integration/test_reports_api.py`.
"""

import json
from collections.abc import Callable, Iterator

import pytest
from fastapi import FastAPI

from app.core import db
from app.core.config import Settings, get_settings
from app.core.errors import ErrorCode
from app.main import create_app
from tests.asgi import Response
from tests.reports import (
    MISSING,
    TEST_PEPPER,
    new_device_id,
    post_report,
    report_meta,
    sample_photo,
)


@pytest.fixture
def app(
    make_settings: Callable[..., Settings], monkeypatch: pytest.MonkeyPatch
) -> Iterator[FastAPI]:
    for var in ("DATABASE_URL", "DB_APP_PASSWORD"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("DEVICE_ID_PEPPER", TEST_PEPPER)
    caches = (get_settings, db.get_engine, db.get_sessionmaker)
    for cache in caches:
        cache.cache_clear()
    yield create_app(make_settings())
    for cache in caches:
        cache.cache_clear()


def _error(response: Response, status: int, code: ErrorCode) -> str:
    assert response.status == status, response.text
    body = response.json()
    assert body["error"]["code"] == code.value
    return body["error"]["message"]


@pytest.mark.parametrize(
    "device_id",
    [None, "A" * 42, "A" * 44, "A" * 42 + "+", "A" * 42 + "/"],
    ids=["absent", "42-caracteres", "44-caracteres", "plus", "barre"],
)
def test_invalid_device_id_is_400_before_the_body(app: FastAPI, device_id: str | None) -> None:
    # Corps invalide aussi : le principal est contrôlé d'abord.
    response = post_report(app, device_id, None, None)
    _error(response, 400, ErrorCode.INVALID_DEVICE_ID)


def test_authorization_header_is_401(app: FastAPI) -> None:
    response = post_report(
        app, new_device_id(), report_meta(), sample_photo(), headers={"Authorization": "Bearer x"}
    )
    _error(response, 401, ErrorCode.INVALID_TOKEN)


@pytest.mark.parametrize(
    ("meta", "photo", "named"),
    [
        (report_meta(), None, "photo"),
        (None, b"jpeg", "meta"),
        ("{pas du json", b"jpeg", "meta"),
        (report_meta(lat=MISSING), b"jpeg", "meta.lat"),
        (report_meta(heap_size=MISSING), b"jpeg", "meta.heap_size"),
    ],
    ids=["sans-photo", "sans-meta", "meta-illisible", "sans-lat", "sans-taille"],
)
def test_missing_or_invalid_field_is_named(
    app: FastAPI, meta: dict | str | None, photo: bytes | None, named: str
) -> None:
    message = _error(
        post_report(app, new_device_id(), meta, photo), 422, ErrorCode.VALIDATION_ERROR
    )
    assert named in message


def test_validation_error_does_not_echo_the_meta(app: FastAPI) -> None:
    meta = report_meta(comment="Zx7-" + "y" * 300)
    response = post_report(app, new_device_id(), meta, sample_photo())
    _error(response, 422, ErrorCode.VALIDATION_ERROR)
    assert "Zx7" not in response.text
    assert json.dumps(meta["lat"]) not in response.text


def test_openapi_describes_a_multipart_body(app: FastAPI) -> None:
    operation = app.openapi()["paths"]["/v1/reports"]["post"]
    content = operation["requestBody"]["content"]
    assert list(content) == ["multipart/form-data"]
    assert "201" in operation["responses"]
