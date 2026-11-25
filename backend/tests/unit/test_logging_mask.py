"""Masquage des données sensibles dans les journaux (AD-10, AD-23) et journal d'accès."""

import json
import logging
from collections.abc import Callable

import pytest

from app.core.config import Settings
from app.core.logging import MASK, get_logger, mask_sensitive
from app.main import create_app
from tests.asgi import request
from tests.support import sample_active_zone

SENSITIVE = {
    "phone": "+221770000000",
    "token": "tok-secret-1",
    "otp": "123456",
    "x-device-id": "dev-id-AAAA",
    "lat": 14.6928,
    "lng": -17.4467,
}


def _json_lines(out: str) -> list[dict]:
    return [json.loads(line) for line in out.splitlines() if line.strip()]


def test_processor_masks_sensitive_keys() -> None:
    event = mask_sensitive(None, "info", {"event": "x", "keep": "visible", **SENSITIVE})
    assert event["keep"] == "visible"
    for key in SENSITIVE:
        assert event[key] == MASK


@pytest.mark.parametrize("key", ["PHONE", "Token", "OTP", "X-Device-Id", "x_device_id", "LAT"])
def test_processor_is_case_insensitive(key: str) -> None:
    assert mask_sensitive(None, "info", {key: "valeur"})[key] == MASK


@pytest.mark.parametrize(
    "key",
    [
        "phone_number",
        "access_token",
        "refresh_token",
        "latitude",
        "longitude",
        "device_id",
        "position",
        "location",
        "password",
        "secret",
        "pepper",
        "cookie",
        "set-cookie",
        "Set-Cookie",
        "authorization",
        "Proxy-Authorization",
        "otp_code",
    ],
)
def test_processor_masks_key_variants(key: str) -> None:
    assert mask_sensitive(None, "info", {key: "valeur"})[key] == MASK


@pytest.mark.parametrize("key", ["lat", "start_lat", "user-lng", "otp", "otp_code", "OTP-Code"])
def test_short_fragments_masked_as_segments(key: str) -> None:
    assert mask_sensitive(None, "info", {key: "valeur"})[key] == MASK


@pytest.mark.parametrize(
    "key",
    [
        "event",
        "route",
        "method",
        "status",
        "role",
        "duration_ms",
        "platform",
        "translation",
        "latency_ms",
        "template",
        "footprint",
    ],
)
def test_access_log_fields_are_not_masked(key: str) -> None:
    assert mask_sensitive(None, "info", {key: "valeur"})[key] == "valeur"


def test_processor_masks_nested_values() -> None:
    event = mask_sensitive(
        None,
        "info",
        {"headers": {"X-Device-Id": "abc", "accept": "json"}, "points": [{"lat": 1, "lng": 2}]},
    )
    assert event["headers"] == {"X-Device-Id": MASK, "accept": "json"}
    assert event["points"] == [{"lat": MASK, "lng": MASK}]


def test_structlog_output_is_masked(capsys: pytest.CaptureFixture[str]) -> None:
    get_logger("test.mask").info("report_received", report="TC-2026-000001", **SENSITIVE)
    out = capsys.readouterr().out
    (line,) = _json_lines(out)
    assert line["event"] == "report_received"
    assert line["report"] == "TC-2026-000001"
    for key, value in SENSITIVE.items():
        assert line[key] == MASK
        assert str(value) not in out


def test_stdlib_output_is_masked(capsys: pytest.CaptureFixture[str]) -> None:
    logging.getLogger("test.stdlib").warning("library", extra={"token": "tok-secret-2"})
    out = capsys.readouterr().out
    assert "tok-secret-2" not in out
    (line,) = _json_lines(out)
    assert line["event"] == "library"
    assert line["token"] == MASK


def test_access_log_line(
    make_settings: Callable[..., Settings], capsys: pytest.CaptureFixture[str]
) -> None:
    app = create_app(make_settings())
    app.state.active_zone = sample_active_zone()
    capsys.readouterr()
    response = request(
        app,
        "GET",
        "/v1/config?lat=14.69&lng=-17.44",
        headers={"X-Device-Id": "dev-id-BBBB", "Authorization": "Bearer tok-secret-3"},
    )
    assert response.status == 200
    out = capsys.readouterr().out
    access = [line for line in _json_lines(out) if line.get("event") == "request"]
    assert len(access) == 1
    entry = access[0]
    assert entry["request_id"] == response.headers["x-request-id"]
    assert entry["route"] == "/v1/config"
    assert entry["method"] == "GET"
    assert entry["status"] == 200
    assert entry["role"] == "anonymous"
    assert isinstance(entry["duration_ms"], float | int)
    # Ni paramètres, ni en-têtes : aucune Position, aucun identifiant d'appareil.
    for leaked in ("14.69", "-17.44", "dev-id-BBBB", "tok-secret-3"):
        assert leaked not in out


def test_access_log_uses_route_template(
    make_settings: Callable[..., Settings], capsys: pytest.CaptureFixture[str]
) -> None:
    app = create_app(make_settings())
    app.state.active_zone = sample_active_zone()

    @app.get("/v1/_test/reports/{report_id}")
    async def read(report_id: str) -> dict[str, str]:
        return {"id": report_id}

    capsys.readouterr()
    request(app, "GET", "/v1/_test/reports/TC-2026-000042")
    request(app, "GET", "/v1/nope/TC-2026-000043")
    request(app, "GET", "/docs")
    request(app, "DELETE", "/v1/config")
    out = capsys.readouterr().out
    routes = [line["route"] for line in _json_lines(out) if line.get("event") == "request"]
    assert routes == ["/v1/_test/reports/{report_id}", "<unmatched>", "/docs", "/v1/config"]
    assert "TC-2026-000042" not in out and "TC-2026-000043" not in out


def test_uvicorn_access_log_is_silenced(capsys: pytest.CaptureFixture[str]) -> None:
    logging.getLogger("uvicorn.access").info('1.2.3.4 - "GET /v1/x?lat=14.69 HTTP/1.1" 200')
    assert "14.69" not in capsys.readouterr().out


def test_probe_access_lines_are_debug(
    make_settings: Callable[..., Settings], capsys: pytest.CaptureFixture[str]
) -> None:
    app = create_app(make_settings())
    app.state.active_zone = sample_active_zone()
    capsys.readouterr()
    for path in ("/healthz", "/metrics", "/v1/config"):
        request(app, "GET", path)
    out = capsys.readouterr().out
    # Niveau INFO : seule la route métier écrit une ligne d'accès.
    routes = [line["route"] for line in _json_lines(out) if line.get("event") == "request"]
    assert routes == ["/v1/config"]
    # Les sondes restent comptées dans les métriques.
    metrics = request(app, "GET", "/metrics").text
    assert 'route="/healthz",status="200"' in metrics


def test_probe_access_lines_visible_in_debug(
    make_settings: Callable[..., Settings], capsys: pytest.CaptureFixture[str]
) -> None:
    app = create_app(make_settings(log_level="DEBUG"))
    app.state.active_zone = sample_active_zone()
    capsys.readouterr()
    request(app, "GET", "/healthz")
    lines = [
        line for line in _json_lines(capsys.readouterr().out) if line.get("event") == "request"
    ]
    assert [(line["route"], line["level"]) for line in lines] == [("/healthz", "debug")]
