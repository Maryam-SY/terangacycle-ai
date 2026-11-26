"""`POST /v1/reports` sans base (story 1.11) : garde des en-têtes, principal, puis `meta`
et photo.

Ces refus ont lieu avant le service : la base n'est pas configurée ici, et tout appel au
service répondrait 500. Le parcours complet (consentement, Zone, photo, écriture) est
vérifié sur la pile réelle par `tests/integration/test_reports_api.py`.
"""

import asyncio
import json
from collections.abc import Callable, Iterator

import pytest
from fastapi import FastAPI
from starlette.types import Message

from app.core import db
from app.core.config import Settings, get_settings
from app.core.errors import ErrorCode
from app.main import create_app
from app.modules.reports.router import MAX_REPORT_BODY_BYTES
from tests.asgi import Response, request
from tests.reports import (
    MISSING,
    PATH,
    new_device_id,
    post_report,
    report_meta,
    sample_photo,
)

MALFORMED_MULTIPART = b"--pas-une-limite\r\nn'importe quoi"


@pytest.fixture
def app(
    make_settings: Callable[..., Settings], monkeypatch: pytest.MonkeyPatch
) -> Iterator[FastAPI]:
    for var in ("DATABASE_URL", "DB_APP_PASSWORD"):
        monkeypatch.delenv(var, raising=False)
    caches = (get_settings, db.get_engine, db.get_sessionmaker)
    for cache in caches:
        cache.cache_clear()
    yield create_app(make_settings())
    for cache in caches:
        cache.cache_clear()


def _error(response: Response, status: int, code: ErrorCode) -> str:
    assert response.status == status, response.text
    body = response.json()
    assert set(body["error"]) == {"code", "message", "request_id"}
    assert body["error"]["code"] == code.value
    assert body["error"]["request_id"] == response.headers["x-request-id"]
    return body["error"]["message"]


def _without_reading_the_body(app: FastAPI, headers: dict[str, str]) -> Response:
    """Requête dont le corps ne peut pas être lu : `receive` échoue s'il est appelé."""
    reads: list[str] = []
    response = Response(status=0)

    async def receive() -> Message:
        reads.append("corps lu")
        raise AssertionError("le corps a été lu avant le refus")

    async def send(message: Message) -> None:
        if message["type"] == "http.response.start":
            response.status = message["status"]
            response.headers = {k.decode().lower(): v.decode() for k, v in message["headers"]}
        elif message["type"] == "http.response.body":
            response.body += message.get("body", b"")

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": PATH,
        "raw_path": PATH.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        "client": ("127.0.0.1", 50000),
        "server": ("testserver", 80),
    }
    asyncio.run(app(scope, receive, send))
    assert reads == []
    return response


@pytest.mark.parametrize(
    "device_id",
    [None, "A" * 42, "A" * 44, "A" * 42 + "+", "A" * 42 + "/"],
    ids=["absent", "42-caracteres", "44-caracteres", "plus", "barre"],
)
def test_invalid_device_id_is_400_before_the_body(app: FastAPI, device_id: str | None) -> None:
    # Corps invalide aussi : le principal est contrôlé d'abord.
    response = post_report(app, device_id, None, None)
    _error(response, 400, ErrorCode.INVALID_DEVICE_ID)


@pytest.mark.parametrize(
    "headers",
    [{}, {"x-device-id": "A" * 42}, {"authorization": "Bearer x"}],
    ids=["sans-appareil", "appareil-invalide", "jeton-sans-appareil"],
)
def test_malformed_multipart_without_device_is_400_not_a_parse_error(
    app: FastAPI, headers: dict[str, str]
) -> None:
    response = request(
        app,
        "POST",
        PATH,
        body=MALFORMED_MULTIPART,
        headers={"content-type": "multipart/form-data; boundary=autre", **headers},
    )
    _error(response, 400, ErrorCode.INVALID_DEVICE_ID)


def test_headers_are_checked_without_reading_the_body(app: FastAPI) -> None:
    multipart = {"content-type": "multipart/form-data; boundary=x", "content-length": "100"}
    response = _without_reading_the_body(app, multipart)
    _error(response, 400, ErrorCode.INVALID_DEVICE_ID)
    device = {**multipart, "x-device-id": new_device_id()}
    response = _without_reading_the_body(app, {**device, "authorization": "Bearer x"})
    _error(response, 401, ErrorCode.INVALID_TOKEN)
    response = _without_reading_the_body(
        app, {**device, "content-length": str(MAX_REPORT_BODY_BYTES + 1)}
    )
    _error(response, 413, ErrorCode.PHOTO_TOO_LARGE)


def test_body_of_2_mib_is_not_refused_by_the_guard(app: FastAPI) -> None:
    """À la limite, la garde laisse passer : la photo est refusée plus loin (meta d'abord)."""
    response = post_report(
        app,
        new_device_id(),
        "{pas du json",
        b"x" * (MAX_REPORT_BODY_BYTES - 1024),
    )
    assert "meta" in _error(response, 422, ErrorCode.VALIDATION_ERROR)


def test_device_id_is_checked_before_the_token(app: FastAPI) -> None:
    response = post_report(app, None, None, None, headers={"Authorization": "Bearer x"})
    _error(response, 400, ErrorCode.INVALID_DEVICE_ID)


def test_authorization_header_is_401(app: FastAPI) -> None:
    response = post_report(
        app, new_device_id(), report_meta(), sample_photo(), headers={"Authorization": "Bearer x"}
    )
    _error(response, 401, ErrorCode.INVALID_TOKEN)


def test_other_routes_are_not_guarded(app: FastAPI) -> None:
    assert request(app, "GET", "/healthz").status == 200


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


def test_openapi_describes_a_multipart_body_and_the_error_contract(app: FastAPI) -> None:
    operation = app.openapi()["paths"]["/v1/reports"]["post"]
    content = operation["requestBody"]["content"]
    assert list(content) == ["multipart/form-data"]
    responses = operation["responses"]
    created = {"$ref": "#/components/schemas/ReportCreated"}
    # 201 : création ; 200 : renvoi idempotent (story 1.12), mêmes champs.
    for status in ("201", "200"):
        assert responses[status]["content"]["application/json"]["schema"] == created, status
    assert "client_uuid" in responses["200"]["description"]
    assert "client_uuid_conflict" in responses["409"]["description"]
    for status in ("400", "401", "409", "413", "415", "422"):
        schema = responses[status]["content"]["application/json"]["schema"]
        assert schema == {"$ref": "#/components/schemas/ErrorResponse"}, status
