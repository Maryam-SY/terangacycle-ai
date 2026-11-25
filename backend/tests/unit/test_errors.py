"""Enveloppe d'erreur unique, codes énumérés et `request_id` (AD-11)."""

import json
import uuid
from collections.abc import Callable

import pytest
from fastapi import FastAPI
from pydantic import BaseModel

from app.core.config import Settings
from app.core.errors import (
    MAX_NAMED_FIELDS,
    DomainError,
    ErrorCode,
    field_of,
    validation_error,
    validation_message,
)
from app.core.errors.codes import DEFAULT_MESSAGES
from app.main import create_app
from tests.asgi import Response, request

SECRET_DETAIL = "detail-interne-Kp3"  # noqa: S105 (texte factice)


class Item(BaseModel):
    name: str
    size: int


@pytest.fixture
def app(make_settings: Callable[..., Settings]) -> FastAPI:
    application = create_app(make_settings())

    @application.post("/v1/_test/items")
    async def create_item(item: Item) -> Item:
        return item

    @application.get("/v1/_test/boom")
    async def boom() -> None:
        raise RuntimeError(SECRET_DETAIL)

    @application.get("/v1/_test/boom-sync")
    def boom_sync() -> None:
        raise ValueError(SECRET_DETAIL)

    @application.get("/v1/_test/domain")
    async def domain() -> None:
        raise DomainError(ErrorCode.NOT_FOUND, 404, "Signalement introuvable.")

    @application.get("/v1/_test/domain-default")
    async def domain_default() -> None:
        raise DomainError(ErrorCode.NOT_FOUND, 404)

    return application


def _assert_envelope(response: Response, status: int, code: ErrorCode) -> dict:
    assert response.status == status
    body = response.json()
    assert set(body) == {"error"}
    error = body["error"]
    assert set(error) == {"code", "message", "request_id"}
    assert error["code"] == code.value
    assert error["message"]
    # request_id généré par le serveur (UUID4) et renvoyé dans X-Request-ID.
    assert uuid.UUID(error["request_id"]).version == 4
    assert response.headers["x-request-id"] == error["request_id"]
    return error


def test_unknown_route_is_not_found(app: FastAPI) -> None:
    response = request(app, "GET", "/v1/inexistant")
    error = _assert_envelope(response, 404, ErrorCode.NOT_FOUND)
    assert error["message"] == DEFAULT_MESSAGES[ErrorCode.NOT_FOUND]


def test_client_request_id_is_ignored(app: FastAPI) -> None:
    response = request(app, "GET", "/v1/inexistant", headers={"X-Request-ID": "client-chosen"})
    error = _assert_envelope(response, 404, ErrorCode.NOT_FOUND)
    assert error["request_id"] != "client-chosen"


def test_wrong_method_is_method_not_allowed(app: FastAPI) -> None:
    response = request(app, "DELETE", "/healthz")
    _assert_envelope(response, 405, ErrorCode.METHOD_NOT_ALLOWED)
    assert "GET" in response.headers.get("allow", "")


@pytest.mark.parametrize(
    "payload",
    [{"name": "x"}, {"name": "x", "size": "pas-un-nombre"}],
    ids=["champ-manquant", "mauvais-type"],
)
def test_invalid_body_is_validation_error(app: FastAPI, payload: dict) -> None:
    response = request(app, "POST", "/v1/_test/items", json_body=payload)
    _assert_envelope(response, 422, ErrorCode.VALIDATION_ERROR)


@pytest.mark.parametrize(
    ("payload", "named"),
    [({"name": "x"}, "size"), ({"size": 2}, "name"), ({}, "name, size")],
    ids=["size", "name", "deux"],
)
def test_validation_error_names_the_field(app: FastAPI, payload: dict, named: str) -> None:
    response = request(app, "POST", "/v1/_test/items", json_body=payload)
    error = _assert_envelope(response, 422, ErrorCode.VALIDATION_ERROR)
    assert named in error["message"]


def test_validation_message_never_echoes_a_value(app: FastAPI) -> None:
    response = request(
        app, "POST", "/v1/_test/items", json_body={"name": "x", "size": SECRET_DETAIL}
    )
    error = _assert_envelope(response, 422, ErrorCode.VALIDATION_ERROR)
    assert "size" in error["message"]
    assert SECRET_DETAIL not in response.text


def test_malformed_json_is_validation_error(app: FastAPI) -> None:
    response = request(
        app,
        "POST",
        "/v1/_test/items",
        body=b"{pas du json",
        headers={"content-type": "application/json"},
    )
    _assert_envelope(response, 422, ErrorCode.VALIDATION_ERROR)


def test_valid_body_passes(app: FastAPI) -> None:
    response = request(app, "POST", "/v1/_test/items", json_body={"name": "x", "size": 2})
    assert response.status == 200
    assert response.json() == {"name": "x", "size": 2}
    assert uuid.UUID(response.headers["x-request-id"]).version == 4


@pytest.mark.parametrize("path", ["/v1/_test/boom", "/v1/_test/boom-sync"])
def test_unexpected_exception_is_internal_error(
    app: FastAPI, path: str, capsys: pytest.CaptureFixture[str]
) -> None:
    response = request(app, "GET", path)
    error = _assert_envelope(response, 500, ErrorCode.INTERNAL_ERROR)
    # Aucune trace ni détail interne dans le corps…
    assert SECRET_DETAIL not in response.text
    assert "Traceback" not in response.text
    # … mais la trace complète dans le journal, avec le request_id.
    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines() if line]
    failures = [line for line in lines if line.get("event") == "unhandled_exception"]
    assert len(failures) == 1
    assert failures[0]["request_id"] == error["request_id"]
    assert "Traceback" in failures[0]["exception"]
    assert SECRET_DETAIL in failures[0]["exception"]


def test_domain_error_uses_its_code_and_status(app: FastAPI) -> None:
    response = request(app, "GET", "/v1/_test/domain")
    error = _assert_envelope(response, 404, ErrorCode.NOT_FOUND)
    assert error["message"] == "Signalement introuvable."


def test_domain_error_default_message(app: FastAPI) -> None:
    response = request(app, "GET", "/v1/_test/domain-default")
    error = _assert_envelope(response, 404, ErrorCode.NOT_FOUND)
    assert error["message"] == DEFAULT_MESSAGES[ErrorCode.NOT_FOUND]


@pytest.mark.parametrize(
    ("loc", "prefix", "expected"),
    [
        (("body", "photo"), None, "photo"),
        (("header", "x-device-id"), None, "x-device-id"),
        (("body",), None, "body"),
        (("items", 0, "name"), None, "items.0.name"),
        (("lat",), "meta", "meta.lat"),
        (("consent", "training"), "meta", "meta.consent.training"),
        ((), "meta", "meta"),
    ],
)
def test_field_of(loc: tuple, prefix: str | None, expected: str) -> None:
    assert field_of(loc, prefix) == expected


def test_validation_message_is_bounded_and_sanitized() -> None:
    names = [f"champ{i}" for i in range(MAX_NAMED_FIELDS + 2)]
    message = validation_message(names)
    assert all(name in message for name in names[:MAX_NAMED_FIELDS])
    assert names[-1] not in message and "…" in message
    # Nom fourni par le client (clé inconnue) : assaini, borné.
    hostile = validation_message(['<script>"x"</script>' + "a" * 200])
    assert "<" not in hostile and '"' not in hostile
    assert len(hostile) < 150
    assert validation_message([]) == DEFAULT_MESSAGES[ErrorCode.VALIDATION_ERROR]


def test_validation_error_is_a_422_domain_error() -> None:
    error = validation_error(["meta.lat", "meta.lat", "photo"])
    assert (error.code, error.http_status) == (ErrorCode.VALIDATION_ERROR, 422)
    assert error.message == "La requête est invalide. Champs à vérifier : meta.lat, photo."


def test_domain_error_rejects_unknown_code() -> None:
    with pytest.raises(ValueError):
        DomainError("code_inconnu", 400)


def test_domain_error_code_and_str() -> None:
    exc = DomainError("not_found", 404)
    assert exc.code is ErrorCode.NOT_FOUND
    assert str(exc) == exc.message == DEFAULT_MESSAGES[ErrorCode.NOT_FOUND]
    custom = DomainError(ErrorCode.NOT_FOUND, 404, "Signalement introuvable.")
    assert str(custom) == custom.message == "Signalement introuvable."


def test_every_code_has_a_default_message() -> None:
    assert set(DEFAULT_MESSAGES) == set(ErrorCode)
    assert {code.value for code in ErrorCode} == {
        "not_found",
        "method_not_allowed",
        "validation_error",
        "internal_error",
        "unsupported_media_type",
        "photo_too_large",
        "photo_too_many_pixels",
        "photo_unreadable",
        "storage_unavailable",
        "invalid_device_id",
        "invalid_token",
        "consent_required",
        "outside_active_zone",
    }


def test_outside_active_zone_message_is_the_story_text() -> None:
    assert DEFAULT_MESSAGES[ErrorCode.OUTSIDE_ACTIVE_ZONE] == (
        "TerangaCycle n'est pas encore actif ici."
    )


def test_error_codes_are_exported_in_openapi(app: FastAPI) -> None:
    schemas = app.openapi()["components"]["schemas"]
    assert set(schemas["ErrorCode"]["enum"]) == {code.value for code in ErrorCode}
    assert "ErrorResponse" in schemas
