"""Settings : URL de base déduites des secrets, règle ENV/DEMO_MODE, secrets masqués."""

from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError
from sqlalchemy import URL, make_url

from app.core.config import Settings
from app.core.enums import Env

# Valeurs factices, propres à ces tests.
APP_PASSWORD = "app-pw-Zx9"  # noqa: S105
MIGRATOR_PASSWORD = "migrator-pw-Qk4"  # noqa: S105

_ENV_VARS = [
    "ENV",
    "DEMO_MODE",
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
def secrets_dir(tmp_path: Path) -> Path:
    (tmp_path / "db_app_password").write_text(APP_PASSWORD + "\n", encoding="utf-8")
    (tmp_path / "db_migrator_password").write_text(MIGRATOR_PASSWORD, encoding="utf-8")
    return tmp_path


def _url(secret: SecretStr | None) -> URL:
    assert secret is not None
    return make_url(secret.get_secret_value())


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


def test_repr_does_not_leak_passwords(secrets_dir: Path) -> None:
    settings = Settings(_secrets_dir=secrets_dir)
    for text in (repr(settings), str(settings), str(settings.model_dump())):
        assert APP_PASSWORD not in text
        assert MIGRATOR_PASSWORD not in text


@pytest.mark.parametrize(
    ("env", "demo_mode"),
    [(Env.DEV, False), (Env.DEV, True), (Env.DEMO, True), (Env.PROD, False)],
)
def test_allowed_env_demo_mode(env: Env, demo_mode: bool, tmp_path: Path) -> None:
    settings = Settings(_secrets_dir=tmp_path, env=env, demo_mode=demo_mode)
    assert (settings.env, settings.demo_mode) == (env, demo_mode)


@pytest.mark.parametrize(("env", "demo_mode"), [(Env.PROD, True), (Env.DEMO, False)])
def test_refused_env_demo_mode(env: Env, demo_mode: bool, tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="DEMO_MODE"):
        Settings(_secrets_dir=tmp_path, env=env, demo_mode=demo_mode)
