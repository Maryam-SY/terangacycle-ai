"""Settings : URL de base, règle ENV/DEMO_MODE, inventaire des secrets (AD-14, AD-26)."""

import json
import logging
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError
from pydantic_settings import SettingsError
from sqlalchemy import URL, make_url

from app.core import config
from app.core.config import (
    REQUIRED_SECRETS,
    ConfigError,
    MigratorSettings,
    Settings,
    load_settings,
    load_settings_or_exit,
)
from app.core.enums import Env
from tests.support import fake_secret_value

BACKEND = Path(__file__).resolve().parents[2]

# Valeurs factices, propres à ces tests.
APP_PASSWORD = "app-pw-Zx9"  # noqa: S105
MIGRATOR_PASSWORD = "migrator-pw-Qk4"  # noqa: S105

_ENV_VARS = [
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
    "DB_APP_USER",
    "DB_MIGRATOR_USER",
    "DB_APP_PASSWORD",
    "DB_MIGRATOR_PASSWORD",
    "DATABASE_URL",
    "MIGRATOR_DATABASE_URL",
]


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in _ENV_VARS:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def secrets_dir(full_secrets_dir: Path) -> Path:
    (full_secrets_dir / "db_app_password").write_text(APP_PASSWORD + "\n", encoding="utf-8")
    (full_secrets_dir / "db_migrator_password").write_text(MIGRATOR_PASSWORD, encoding="utf-8")
    return full_secrets_dir


def _url(secret: SecretStr | None) -> URL:
    assert secret is not None
    return make_url(secret.get_secret_value())


def _all_secret_values() -> list[str]:
    return [fake_secret_value(name) for name in REQUIRED_SECRETS]


# --- URL de base -----------------------------------------------------------------


def test_urls_derived_from_secrets(secrets_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_HOST", "dbhost")
    monkeypatch.setenv("DB_PORT", "6543")
    monkeypatch.setenv("DB_NAME", "tcdb")
    settings = Settings(_secrets_dir=secrets_dir)

    app = _url(settings.database_url)
    assert app.drivername == "postgresql+psycopg"
    assert (app.username, app.password) == ("teranga_app", APP_PASSWORD)
    assert (app.host, app.port, app.database) == ("dbhost", 6543, "tcdb")

    migrator = _url(settings.migrator_database_url)
    assert (migrator.username, migrator.password) == ("teranga_migrator", MIGRATOR_PASSWORD)
    assert (migrator.host, migrator.port, migrator.database) == ("dbhost", 6543, "tcdb")


def test_explicit_database_url_is_kept(secrets_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    explicit = "postgresql+psycopg://someone:pw@elsewhere:5433/other"
    monkeypatch.setenv("DATABASE_URL", explicit)
    settings = Settings(_secrets_dir=secrets_dir)
    assert settings.database_url is not None
    assert settings.database_url.get_secret_value() == explicit
    # L'URL de migration, non fournie, reste déduite des secrets.
    assert _url(settings.migrator_database_url).username == "teranga_migrator"


def test_urls_stay_none_without_password_secrets(tmp_path: Path) -> None:
    settings = Settings(_secrets_dir=tmp_path)
    assert settings.database_url is None
    assert settings.migrator_database_url is None


def test_repr_does_not_leak_secrets(secrets_dir: Path) -> None:
    settings = Settings(_secrets_dir=secrets_dir)
    for text in (repr(settings), str(settings), str(settings.model_dump())):
        assert APP_PASSWORD not in text
        assert MIGRATOR_PASSWORD not in text
        for value in _all_secret_values():
            assert value not in text


# --- ENV et DEMO_MODE ------------------------------------------------------------


@pytest.mark.parametrize(
    ("env", "demo_mode"),
    [(Env.DEV, False), (Env.DEV, True), (Env.DEMO, True), (Env.PROD, False)],
)
def test_allowed_env_demo_mode(
    env: Env, demo_mode: bool, make_settings: Callable[..., Settings]
) -> None:
    settings = make_settings(env=env, demo_mode=demo_mode)
    assert (settings.env, settings.demo_mode) == (env, demo_mode)


@pytest.mark.parametrize(("env", "demo_mode"), [(Env.PROD, True), (Env.DEMO, False)])
def test_refused_env_demo_mode(
    env: Env, demo_mode: bool, make_settings: Callable[..., Settings]
) -> None:
    with pytest.raises(ValidationError, match="DEMO_MODE"):
        make_settings(env=env, demo_mode=demo_mode)


@pytest.mark.parametrize(
    ("variables", "expected"),
    [
        ({"ENV": "prod", "DEMO_MODE": "true"}, "DEMO_MODE est interdit"),
        ({"ENV": "demo"}, "ENV=demo exige DEMO_MODE=true"),
        ({"ENV": "staging"}, "ENV :"),
    ],
)
def test_load_settings_refuses_invalid_config(
    variables: dict[str, str],
    expected: str,
    full_secrets_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name, value in variables.items():
        monkeypatch.setenv(name, value)
    with pytest.raises(ConfigError) as exc_info:
        load_settings(_secrets_dir=full_secrets_dir)
    message = str(exc_info.value)
    assert expected in message
    # Le message ne recopie aucune valeur reçue.
    for value in _all_secret_values():
        assert value not in message


# --- Secrets de l'inventaire AD-26 ----------------------------------------------


def test_inventory_matches_ad26() -> None:
    assert set(REQUIRED_SECRETS) == {
        "jwt_signing_keys",
        "phone_pepper",
        "device_id_pepper",
        "phone_enc_keys",
        "totp_enc_key",
        "vapid_private_key",
        "s3_access_key_id",
        "s3_secret_access_key",
        "alert_webhook_url",
    }


@pytest.mark.parametrize("env", [Env.DEMO, Env.PROD])
def test_all_secrets_present_are_read(env: Env, full_secrets_dir: Path) -> None:
    settings = load_settings(_secrets_dir=full_secrets_dir, env=env, demo_mode=env is Env.DEMO)
    for name in REQUIRED_SECRETS:
        assert getattr(settings, name).get_secret_value() == fake_secret_value(name)
    assert settings.ephemeral_secrets == ()


@pytest.mark.parametrize("env", [Env.DEMO, Env.PROD])
@pytest.mark.parametrize("blank", [False, True], ids=["absent", "vide"])
def test_missing_secret_refuses_start(env: Env, blank: bool, full_secrets_dir: Path) -> None:
    pepper = full_secrets_dir / "phone_pepper"
    if blank:
        pepper.write_text("  \n", encoding="utf-8")
    else:
        pepper.unlink()
    with pytest.raises(ConfigError) as exc_info:
        load_settings(_secrets_dir=full_secrets_dir, env=env, demo_mode=env is Env.DEMO)
    message = str(exc_info.value)
    assert "secret manquant : phone_pepper" in message
    for value in _all_secret_values():
        assert value not in message


def test_all_missing_secrets_are_named(tmp_path: Path) -> None:
    with pytest.raises(ConfigError) as exc_info:
        load_settings(_secrets_dir=tmp_path, env=Env.PROD)
    message = str(exc_info.value)
    assert "secrets manquants : " + ", ".join(REQUIRED_SECRETS) in message


def test_dev_generates_ephemeral_secrets(
    full_secrets_dir: Path, caplog: pytest.LogCaptureFixture
) -> None:
    (full_secrets_dir / "phone_pepper").unlink()
    (full_secrets_dir / "jwt_signing_keys").unlink()
    with caplog.at_level(logging.WARNING, logger="app.core.config"):
        settings = load_settings(_secrets_dir=full_secrets_dir, env=Env.DEV)

    assert settings.ephemeral_secrets == ("jwt_signing_keys", "phone_pepper")
    assert settings.phone_pepper is not None and settings.phone_pepper.get_secret_value()
    assert settings.jwt_signing_keys is not None
    keys = json.loads(settings.jwt_signing_keys.get_secret_value())
    assert len(keys) == 1
    # Les secrets présents sont gardés tels quels.
    assert settings.device_id_pepper is not None
    assert settings.device_id_pepper.get_secret_value() == fake_secret_value("device_id_pepper")
    # Avertissement qui nomme les secrets, sans valeur.
    warning = " ".join(r.getMessage() for r in caplog.records)
    assert "phone_pepper" in warning and "jwt_signing_keys" in warning
    assert settings.phone_pepper.get_secret_value() not in warning


def test_dev_ephemeral_values_differ_between_processes(tmp_path: Path) -> None:
    first = load_settings(_secrets_dir=tmp_path)
    second = load_settings(_secrets_dir=tmp_path)
    assert first.phone_pepper is not None and second.phone_pepper is not None
    assert first.phone_pepper.get_secret_value() != second.phone_pepper.get_secret_value()


def test_migrator_settings_do_not_require_the_inventory(secrets_dir: Path) -> None:
    # Le service migrate ne reçoit que db_migrator_password : l'inventaire n'est pas exigé.
    for name in REQUIRED_SECRETS:
        (secrets_dir / name).unlink()
    settings = load_settings(MigratorSettings, _secrets_dir=secrets_dir, env=Env.PROD)
    assert _url(settings.migrator_database_url).username == "teranga_migrator"
    assert settings.ephemeral_secrets == ()
    assert settings.phone_pepper is None
    # Les règles ENV/DEMO_MODE restent appliquées.
    with pytest.raises(ConfigError, match="DEMO_MODE"):
        load_settings(MigratorSettings, _secrets_dir=secrets_dir, env=Env.PROD, demo_mode=True)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("vapid_private_key", "dev-placeholder-abc"),
        ("s3_access_key_id", "dev-ephemeral-abc"),
        ("alert_webhook_url", "http://localhost/alert-disabled"),
    ],
)
def test_prod_rejects_dev_secret_values(name: str, value: str, full_secrets_dir: Path) -> None:
    (full_secrets_dir / name).write_text(value, encoding="utf-8")
    with pytest.raises(ConfigError) as exc_info:
        load_settings(_secrets_dir=full_secrets_dir, env=Env.PROD)
    message = str(exc_info.value)
    assert f"secret de développement refusé en production : {name}" in message
    assert value not in message
    # En démo, les valeurs du générateur restent acceptées.
    load_settings(_secrets_dir=full_secrets_dir, env=Env.DEMO, demo_mode=True)


@pytest.mark.parametrize("raw", ["", "   "])
def test_empty_model_version_is_none(
    raw: str, monkeypatch: pytest.MonkeyPatch, make_settings: Callable[..., Settings]
) -> None:
    monkeypatch.setenv("MODEL_VERSION", raw)
    assert make_settings().model_version is None


def test_storage_and_model_defaults(make_settings: Callable[..., Settings]) -> None:
    settings = make_settings()
    assert settings.s3_endpoint == "http://garage:3900"
    assert settings.s3_region == "garage"
    assert settings.s3_bucket == "terangacycle-photos"
    assert settings.model_version is None


# --- Refus de démarrer ----------------------------------------------------------


def test_load_settings_or_exit_exits_with_code_1(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("ENV", "staging")
    config.get_settings.cache_clear()
    try:
        with pytest.raises(SystemExit) as exc_info:
            load_settings_or_exit()
    finally:
        config.get_settings.cache_clear()
    assert exc_info.value.code == 1
    assert "startup_refused" in capsys.readouterr().out


@pytest.mark.parametrize(
    "error",
    [OSError(13, "Permission denied", "/run/secrets/phone_pepper"), SettingsError("bad")],
    ids=["oserror", "settingserror"],
)
def test_load_settings_or_exit_catches_read_errors(
    error: Exception, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def broken() -> Settings:
        raise error

    monkeypatch.setattr(config, "get_settings", broken)
    with pytest.raises(SystemExit) as exc_info:
        load_settings_or_exit()
    assert exc_info.value.code == 1
    out = capsys.readouterr().out
    entry = json.loads(out.strip().splitlines()[-1])
    assert entry["event"] == "startup_refused"
    assert entry["reason"] == type(error).__name__


def test_alembic_runs_with_only_the_migrator_secret(tmp_path: Path) -> None:
    """Le service migrate (ENV=demo) n'a que db_migrator_password : la migration passe."""
    secrets = tmp_path / "secrets"
    secrets.mkdir()
    (secrets / "db_migrator_password").write_text(MIGRATOR_PASSWORD, encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k.upper() not in {"ENV", "DEMO_MODE"}}
    env.update(ENV="demo", DEMO_MODE="true", SECRETS_DIR=str(secrets))
    result = subprocess.run(  # noqa: S603 (interpréteur courant, arguments fixes)
        [sys.executable, "-m", "alembic", "upgrade", "head", "--sql"],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert MIGRATOR_PASSWORD not in result.stdout + result.stderr


@pytest.mark.parametrize(
    ("variables", "remove", "expected"),
    [
        ({"ENV": "prod", "DEMO_MODE": "true"}, None, "DEMO_MODE est interdit"),
        ({"ENV": "demo"}, None, "ENV=demo exige DEMO_MODE=true"),
        ({"ENV": "staging"}, None, "ENV :"),
        ({"ENV": "demo", "DEMO_MODE": "true"}, "phone_pepper", "secret manquant : phone_pepper"),
    ],
    ids=["prod-demo-mode", "demo-sans-demo-mode", "env-inconnu", "secret-manquant"],
)
@pytest.mark.parametrize(
    "entrypoint", ["from app.main import create_app; create_app()", "import app.worker"]
)
def test_process_refuses_to_start(
    variables: dict[str, str],
    remove: str | None,
    expected: str,
    entrypoint: str,
    full_secrets_dir: Path,
) -> None:
    """Le processus réel (API ou worker) s'arrête avec un code non nul et un message clair."""
    if remove:
        (full_secrets_dir / remove).unlink()
    env = {k: v for k, v in os.environ.items() if k.upper() not in {"ENV", "DEMO_MODE"}}
    env.update(variables, SECRETS_DIR=str(full_secrets_dir))
    result = subprocess.run(  # noqa: S603 (interpréteur courant, arguments fixes)
        [sys.executable, "-c", entrypoint],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert expected in output
    assert "Traceback" not in output
    for value in _all_secret_values():
        assert value not in output
