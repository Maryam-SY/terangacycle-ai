"""Fixtures communes : environnement neutre, journalisation sur la sortie capturée."""

import os
from collections.abc import Callable
from pathlib import Path

import pytest

from app.core.config import REQUIRED_SECRETS, Settings
from app.core.logging import configure_logging
from tests.support import fake_secret_value

# Variables qui changeraient le résultat des tests si l'hôte les définissait.
_SETTINGS_ENV_VARS = [
    "ENV",
    "DEMO_MODE",
    "LOG_LEVEL",
    "MODEL_VERSION",
    "S3_ENDPOINT",
    "S3_REGION",
    "S3_BUCKET",
    "VALKEY_URL",
    *(name.upper() for name in REQUIRED_SECRETS),
]


@pytest.fixture(autouse=True)
def _neutral_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in _SETTINGS_ENV_VARS:
        if var in os.environ:
            monkeypatch.delenv(var)
    # Journalisation JSON neutre (le gestionnaire suit sys.stdout, capturé par capsys).
    configure_logging("INFO")


@pytest.fixture
def full_secrets_dir(tmp_path: Path) -> Path:
    """Dossier de secrets contenant tout l'inventaire d'AD-26."""
    directory = tmp_path / "secrets"
    directory.mkdir()
    for name in REQUIRED_SECRETS:
        (directory / name).write_text(fake_secret_value(name) + "\n", encoding="utf-8")
    return directory


@pytest.fixture
def make_settings(full_secrets_dir: Path) -> Callable[..., Settings]:
    """Fabrique de `Settings` complètes (tous les secrets présents)."""

    def factory(**overrides: object) -> Settings:
        return Settings(_secrets_dir=full_secrets_dir, **overrides)  # type: ignore[arg-type]

    return factory
