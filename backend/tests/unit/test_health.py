"""Sondes `/healthz`, `/readyz`, `/metrics` et `GET /v1/config` (AD-14, AD-27).

Les vérifications de `/readyz` sont simulées : chacune est mise en échec isolément.
Le test sur la pile réelle est `scripts/smoke_readyz.py`.
"""

import asyncio
import json
from collections.abc import Callable

import pytest
from fastapi import FastAPI
from sqlalchemy.pool import NullPool

from app.core import health
from app.core.clock import now
from app.core.config import Settings
from app.core.enums import Env
from app.main import create_app
from tests.asgi import request


async def _ok(settings: Settings) -> None:
    return None


async def _fails(settings: Settings) -> None:
    raise ConnectionError("dial tcp 10.0.0.7:5432: interne")


async def _hangs(settings: Settings) -> None:
    await asyncio.sleep(10)


@pytest.fixture
def app(make_settings: Callable[..., Settings]) -> FastAPI:
    return create_app(make_settings())


@pytest.fixture
def all_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(health.READINESS_CHECKS):
        monkeypatch.setitem(health.READINESS_CHECKS, name, _ok)


def test_healthz_has_no_dependency(app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    # Toutes les dépendances en panne : la vivacité reste 200.
    for name in list(health.READINESS_CHECKS):
        monkeypatch.setitem(health.READINESS_CHECKS, name, _fails)
    response = request(app, "GET", "/healthz")
    assert response.status == 200
    assert response.json() == {"status": "ok"}


def test_readiness_checks_cover_the_four_dependencies() -> None:
    assert set(health.READINESS_CHECKS) == {"database", "valkey", "storage", "worker"}


def test_readyz_ready_when_all_checks_pass(app: FastAPI, all_ok: None) -> None:
    response = request(app, "GET", "/readyz")
    assert response.status == 200
    assert response.json() == {"status": "ready"}


@pytest.mark.parametrize("failing", ["database", "valkey", "storage", "worker"])
@pytest.mark.parametrize("failure", [_fails, _hangs], ids=["erreur", "délai"])
def test_readyz_not_ready_when_one_check_fails(
    app: FastAPI,
    all_ok: None,
    failing: str,
    failure: Callable,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(health, "CHECK_TIMEOUT_S", 0.2)
    monkeypatch.setitem(health.READINESS_CHECKS, failing, failure)
    response = request(app, "GET", "/readyz")
    assert response.status == 503
    # Statut global seulement, aucun détail interne.
    assert response.json() == {"status": "not_ready"}
    assert "interne" not in response.text and failing not in response.text
    # La cause est dans le journal, sans le message de l'exception.
    out = capsys.readouterr().out
    failures = [
        line
        for line in (json.loads(raw) for raw in out.splitlines() if raw)
        if line.get("event") == "readiness_check_failed"
    ]
    assert [f["check"] for f in failures] == [failing]
    assert "10.0.0.7" not in out


def test_readyz_checks_run_in_parallel(
    app: FastAPI, all_ok: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    def slow(name: str) -> Callable:
        async def check(settings: Settings) -> None:
            calls.append(name)
            await asyncio.sleep(0.3)

        return check

    for name in list(health.READINESS_CHECKS):
        monkeypatch.setitem(health.READINESS_CHECKS, name, slow(name))
    loop_time: list[float] = []

    async def timed() -> bool:
        start = asyncio.get_running_loop().time()
        result = await health.readiness(app.state.settings)
        loop_time.append(asyncio.get_running_loop().time() - start)
        return result

    assert asyncio.run(timed()) is True
    assert len(calls) == 4
    # Quatre vérifications de 0,3 s en parallèle : bien moins que 1,2 s.
    assert loop_time[0] < 0.9


@pytest.mark.parametrize(
    ("raw", "fresh"),
    [
        (None, False),
        (b"pas-un-nombre", False),
        ("ancien", False),
        (bytes([0xFF, 0xFE]), False),
        ("inf", False),
        ("-inf", False),
        ("nan", False),
    ],
)
def test_heartbeat_unreadable(raw: object, fresh: bool) -> None:
    assert health.heartbeat_is_fresh(raw) is fresh  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("age_s", "fresh"),
    [(-4, True), (-6, False), (-3600, False), (0, True), (59.5, True), (60, False), (120, False)],
    ids=["futur-tolere", "futur-refuse", "futur-lointain", "0", "59.5", "60", "120"],
)
def test_heartbeat_age_threshold(age_s: float, fresh: bool) -> None:
    raw = str(now().timestamp() - age_s).encode()
    assert health.heartbeat_is_fresh(raw) is fresh


def test_metrics_exposes_prometheus_format(app: FastAPI) -> None:
    request(app, "GET", "/healthz")
    request(app, "GET", "/v1/inexistant")
    response = request(app, "GET", "/metrics")
    assert response.status == 200
    assert response.headers["content-type"].startswith("text/plain")
    text = response.text
    assert "# TYPE http_requests_total counter" in text
    assert 'http_requests_total{method="GET",route="/healthz",status="200"}' in text
    assert 'route="<unmatched>",status="404"' in text
    assert "http_request_duration_seconds_bucket" in text


def test_metrics_method_label_is_bounded(app: FastAPI) -> None:
    request(app, "FROBNICATE", "/healthz")
    text = request(app, "GET", "/metrics").text
    assert "FROBNICATE" not in text
    assert 'method="OTHER",route="/healthz",status="405"' in text


def test_metrics_hidden_from_openapi(app: FastAPI) -> None:
    assert "/metrics" not in app.openapi()["paths"]


@pytest.mark.parametrize(
    ("env", "demo_mode", "model_version"),
    [(Env.DEMO, True, None), (Env.PROD, False, "1.0.0"), (Env.DEV, False, None)],
)
def test_public_config(
    env: Env,
    demo_mode: bool,
    model_version: str | None,
    make_settings: Callable[..., Settings],
) -> None:
    app = create_app(make_settings(env=env, demo_mode=demo_mode, model_version=model_version))
    response = request(app, "GET", "/v1/config")
    assert response.status == 200
    assert response.json() == {
        "demo_mode": demo_mode,
        "env": env.value,
        "model_version": model_version,
    }


# --- Vérifications réelles, dépendances simulées ----------------------------------


class FakeRedis:
    """Client Valkey simulé : `ping`, `get`, `aclose`."""

    def __init__(self, *, pong: bool = True, value: bytes | None = None) -> None:
        self.pong = pong
        self.value = value
        self.keys: list[str] = []
        self.closed = False

    async def ping(self) -> bool:
        return self.pong

    async def get(self, key: str) -> bytes | None:
        self.keys.append(key)
        return self.value

    async def aclose(self) -> None:
        self.closed = True


class FakeS3:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def head_bucket(self, **kwargs: object) -> dict:
        self.calls.append(kwargs)
        return {}


def _use_redis(monkeypatch: pytest.MonkeyPatch, fake: FakeRedis) -> None:
    monkeypatch.setattr(health, "_redis", lambda settings: fake)


@pytest.mark.parametrize(
    ("value", "ready"),
    [
        (lambda: str(now().timestamp() - 5).encode(), True),
        (lambda: str(now().timestamp() - 61).encode(), False),
        (lambda: None, False),
        (lambda: b"illisible", False),
    ],
    ids=["frais", "ancien", "absent", "illisible"],
)
def test_check_worker(
    value: Callable[[], bytes | None],
    ready: bool,
    make_settings: Callable[..., Settings],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeRedis(value=value())
    _use_redis(monkeypatch, fake)
    settings = make_settings()
    if ready:
        asyncio.run(health.check_worker(settings))
    else:
        with pytest.raises(RuntimeError):
            asyncio.run(health.check_worker(settings))
    assert fake.keys == [health.HEARTBEAT_KEY]
    assert fake.closed


@pytest.mark.parametrize("pong", [True, False])
def test_check_valkey(
    pong: bool, make_settings: Callable[..., Settings], monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeRedis(pong=pong)
    _use_redis(monkeypatch, fake)
    if pong:
        asyncio.run(health.check_valkey(make_settings()))
    else:
        with pytest.raises(RuntimeError):
            asyncio.run(health.check_valkey(make_settings()))
    assert fake.closed


def test_head_bucket_uses_configured_bucket(
    make_settings: Callable[..., Settings], monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeS3()
    built: list[tuple] = []

    def client(*args: str) -> FakeS3:
        built.append(args)
        return fake

    monkeypatch.setattr(health, "_s3_client", client)
    settings = make_settings(s3_bucket="bucket-de-test")
    health._head_bucket(settings)
    assert fake.calls == [{"Bucket": "bucket-de-test"}]
    assert built[0][:2] == (settings.s3_endpoint, settings.s3_region)


def test_head_bucket_without_credentials(make_settings: Callable[..., Settings]) -> None:
    settings = make_settings()
    settings.s3_access_key_id = None
    with pytest.raises(RuntimeError):
        health._head_bucket(settings)


def test_s3_probe_client_configuration() -> None:
    health._s3_client.cache_clear()
    try:
        client = health._s3_client("http://garage:3900", "garage", "AK", "SK")
        config = client.meta.config
        assert (config.connect_timeout, config.read_timeout) == (1, 1)
        assert config.retries["total_max_attempts"] == 1
        assert config.s3["addressing_style"] == "path"
        assert config.request_checksum_calculation == "when_required"
    finally:
        health._s3_client.cache_clear()


def test_probe_engine_bounds_timeouts(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    def fake_create_engine(url: str, **kwargs: object) -> object:
        captured.update(kwargs, url=url)
        return object()

    monkeypatch.setattr(health, "create_engine", fake_create_engine)
    health._probe_engine.cache_clear()
    try:
        health._probe_engine("postgresql+psycopg://u:p@db:5432/x")
    finally:
        health._probe_engine.cache_clear()
    assert captured["connect_args"] == {
        "connect_timeout": 2,
        "options": "-c statement_timeout=2000",
    }
    assert captured["poolclass"] is NullPool
