"""Démarrage de l'API : chargement de la Zone active ou refus (story 1.8).

La lecture en base est simulée ici ; le refus réel (processus uvicorn, base PostGIS) est
vérifié par `tests/integration/test_zones.py`.
"""

import asyncio
import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi import FastAPI
from sqlalchemy.exc import DBAPIError

from app import main
from app.core.config import ConfigError, Settings, load_settings
from app.core.geo import ActiveZone, UnknownZoneError
from app.main import create_app
from tests.asgi import request
from tests.support import sample_active_zone

BACKEND = Path(__file__).resolve().parents[2]


class _Exited(Exception):
    def __init__(self, code: int) -> None:
        self.code = code


@pytest.fixture
def exits(monkeypatch: pytest.MonkeyPatch) -> None:
    """`os._exit` simulé : le test survit et lit le code de sortie."""

    def fake_exit(code: int) -> None:
        raise _Exited(code)

    monkeypatch.setattr(os, "_exit", fake_exit)


async def _start(app: FastAPI) -> None:
    async with app.router.lifespan_context(app):
        pass


def _journal(out: str) -> list[dict]:
    return [json.loads(line) for line in out.splitlines() if line.strip().startswith("{")]


# --- Réglages -------------------------------------------------------------------------


def test_zone_settings_defaults(make_settings: Callable[..., Settings]) -> None:
    settings = make_settings()
    assert settings.active_zone_id == "dakar"
    assert settings.report_accuracy_flag_m == 50


def test_zone_settings_from_environment(
    make_settings: Callable[..., Settings], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ACTIVE_ZONE_ID", " dakar-plateau ")
    monkeypatch.setenv("REPORT_ACCURACY_FLAG_M", "30")
    settings = make_settings()
    assert settings.active_zone_id == "dakar-plateau"
    assert settings.report_accuracy_flag_m == 30


@pytest.mark.parametrize(
    ("overrides", "named"),
    [
        ({"active_zone_id": ""}, "ACTIVE_ZONE_ID"),
        ({"active_zone_id": "   "}, "ACTIVE_ZONE_ID"),
        ({"report_accuracy_flag_m": 0}, "REPORT_ACCURACY_FLAG_M"),
        ({"report_accuracy_flag_m": -5}, "REPORT_ACCURACY_FLAG_M"),
        ({"report_accuracy_flag_m": 1001}, "REPORT_ACCURACY_FLAG_M"),
        ({"report_accuracy_flag_m": "beaucoup"}, "REPORT_ACCURACY_FLAG_M"),
    ],
)
def test_invalid_zone_settings_are_refused(
    overrides: dict[str, object], named: str, full_secrets_dir: Path
) -> None:
    with pytest.raises(ConfigError, match=named):
        load_settings(Settings, _secrets_dir=full_secrets_dir, **overrides)


# --- Lifespan -------------------------------------------------------------------------


def test_lifespan_loads_the_active_zone_once(
    make_settings: Callable[..., Settings], monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    def read(settings: Settings) -> ActiveZone:
        calls.append(settings.active_zone_id)
        return sample_active_zone()

    monkeypatch.setattr(main, "read_active_zone", read)
    app = create_app(make_settings())
    asyncio.run(_start(app))
    assert calls == ["dakar"]
    assert app.state.active_zone == sample_active_zone()
    # La route lit la Zone gardée en mémoire, sans nouvelle lecture.
    assert request(app, "GET", "/v1/config").json()["active_zone"]["id"] == "dakar"
    assert calls == ["dakar"]


def test_unknown_zone_refuses_startup(
    make_settings: Callable[..., Settings],
    monkeypatch: pytest.MonkeyPatch,
    exits: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def read(settings: Settings) -> ActiveZone:
        raise UnknownZoneError(settings.active_zone_id)

    monkeypatch.setattr(main, "read_active_zone", read)
    app = create_app(make_settings(active_zone_id="inexistante"))
    with pytest.raises(_Exited) as exc_info:
        asyncio.run(_start(app))
    assert exc_info.value.code == 1
    (entry,) = [e for e in _journal(capsys.readouterr().out) if e["event"] == "startup_refused"]
    assert "ACTIVE_ZONE_ID" in entry["reason"]


def test_unreachable_database_refuses_startup_without_details(
    make_settings: Callable[..., Settings],
    monkeypatch: pytest.MonkeyPatch,
    exits: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    leak = "postgresql://teranga_app:pw-Zq8@db:5432 lat=14.69"

    def read(settings: Settings) -> ActiveZone:
        raise ConnectionRefusedError(leak)

    monkeypatch.setattr(main, "read_active_zone", read)
    app = create_app(make_settings())
    with pytest.raises(_Exited) as exc_info:
        asyncio.run(_start(app))
    assert exc_info.value.code == 1
    out = capsys.readouterr().out
    (entry,) = [e for e in _journal(out) if e["event"] == "startup_refused"]
    assert entry["reason"] == "base injoignable ou illisible (ConnectionRefusedError)"
    assert "pw-Zq8" not in out and "14.69" not in out


def test_missing_database_url_refuses_startup(
    make_settings: Callable[..., Settings],
    monkeypatch: pytest.MonkeyPatch,
    exits: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    for var in ("DATABASE_URL", "DB_APP_PASSWORD"):
        monkeypatch.delenv(var, raising=False)
    app = create_app(make_settings())
    assert app.state.settings.database_url is None
    with pytest.raises(_Exited) as exc_info:
        asyncio.run(_start(app))
    assert exc_info.value.code == 1
    events = [e["event"] for e in _journal(capsys.readouterr().out)]
    assert "startup_refused" in events


def test_process_exits_with_code_1_when_the_database_is_unreachable() -> None:
    """Processus uvicorn réel : base injoignable → `startup_refused` et code 1 (pas 3)."""
    password = "pw-Kx41"  # noqa: S105 (valeur factice)
    env = {k: v for k, v in os.environ.items() if k.upper() not in {"ENV", "DEMO_MODE"}}
    env.update(
        ENV="dev",
        # Port 1 : connexion refusée aussitôt, sans attendre le délai.
        DATABASE_URL=f"postgresql+psycopg://teranga_app:{password}@127.0.0.1:1/terangacycle",
        SECRETS_DIR="/nonexistent",
    )
    result = subprocess.run(  # noqa: S603 (interpréteur courant, arguments fixes)
        [sys.executable, "-m", "uvicorn", "--factory", "app.main:create_app", "--port", "0"],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 1, output
    assert "startup_refused" in output
    assert password not in output


class _PgError(Exception):
    def __init__(self, sqlstate: str) -> None:
        super().__init__("message du pilote : postgresql://teranga_app:pw-Zq8@db")
        self.sqlstate = sqlstate


@pytest.mark.parametrize(
    ("sqlstate", "reason"),
    [
        ("42P01", "table zones absente : migration 0002 non appliquée"),
        ("42501", "droit de lecture manquant sur zones"),
        ("08006", "base injoignable ou illisible (DBAPIError)"),
    ],
)
def test_startup_reason_names_the_sqlstate(
    sqlstate: str,
    reason: str,
    make_settings: Callable[..., Settings],
    monkeypatch: pytest.MonkeyPatch,
    exits: None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def read(settings: Settings) -> ActiveZone:
        raise DBAPIError("SELECT 1", None, _PgError(sqlstate))

    monkeypatch.setattr(main, "read_active_zone", read)
    app = create_app(make_settings())
    with pytest.raises(_Exited):
        asyncio.run(_start(app))
    out = capsys.readouterr().out
    (entry,) = [e for e in _journal(out) if e["event"] == "startup_refused"]
    assert entry["reason"] == reason
    assert "pw-Zq8" not in out


def test_startup_connection_has_a_statement_timeout(
    make_settings: Callable[..., Settings], monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: dict[str, object] = {}

    def fake_create_engine(url: str, **kwargs: object) -> object:
        seen.update(kwargs)
        raise RuntimeError("arrêt du test")

    monkeypatch.setattr(main, "create_engine", fake_create_engine)
    settings = make_settings(database_url="postgresql+psycopg://u:p@127.0.0.1:1/x")
    with pytest.raises(RuntimeError, match="arrêt du test"):
        main.read_active_zone(settings)
    assert seen["connect_args"] == {"connect_timeout": 5, "options": "-c statement_timeout=5000"}
    assert seen["hide_parameters"] is True
