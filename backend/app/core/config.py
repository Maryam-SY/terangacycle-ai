"""Configuration unique de l'application (AD-14, AD-26).

Toute la configuration passe par `Settings` : variables d'environnement pour les
réglages, fichiers de `/run/secrets/` (secrets Compose) pour les secrets.
"""

import os
from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

from app.core.enums import Env

# Dossier des secrets montés par Compose ; surchargeable pour les tests.
SECRETS_DIR = Path(os.environ.get("SECRETS_DIR", "/run/secrets"))


def _db_url(user: str, password: SecretStr, host: str, port: int, name: str) -> SecretStr:
    """Construit une URL psycopg 3 en échappant le mot de passe, masquée dans les `repr`."""
    return SecretStr(
        URL.create(
            "postgresql+psycopg",
            username=user,
            password=password.get_secret_value(),
            host=host,
            port=port,
            database=name,
        ).render_as_string(hide_password=False)
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Sans dossier de secrets (poste de développement), on ne lit que l'environnement.
        secrets_dir=SECRETS_DIR if SECRETS_DIR.is_dir() else None,
        extra="ignore",
    )

    env: Env = Env.DEV
    demo_mode: bool = False
    log_level: str = "INFO"

    # Base de données : composants non secrets, mots de passe dans /run/secrets/.
    db_host: str = "db"
    db_port: int = 5432
    db_name: str = "terangacycle"
    db_app_user: str = "teranga_app"
    db_migrator_user: str = "teranga_migrator"
    db_app_password: SecretStr | None = None
    db_migrator_password: SecretStr | None = None

    # URL complètes : fournies telles quelles, sinon déduites des composants ci-dessus.
    # Elles contiennent un mot de passe : SecretStr, lues seulement à la création du moteur.
    database_url: SecretStr | None = None
    migrator_database_url: SecretStr | None = None

    valkey_url: str = "redis://valkey:6379/0"

    @model_validator(mode="after")
    def _check_demo_mode(self) -> "Settings":
        # AD-14 : DEMO_MODE interdit en production, exigé par ENV=demo.
        if self.env is Env.PROD and self.demo_mode:
            raise ValueError("DEMO_MODE est interdit quand ENV=prod.")
        if self.env is Env.DEMO and not self.demo_mode:
            raise ValueError("ENV=demo exige DEMO_MODE=true.")
        return self

    @model_validator(mode="after")
    def _derive_database_urls(self) -> "Settings":
        if self.database_url is None and self.db_app_password is not None:
            self.database_url = _db_url(
                self.db_app_user, self.db_app_password, self.db_host, self.db_port, self.db_name
            )
        if self.migrator_database_url is None and self.db_migrator_password is not None:
            self.migrator_database_url = _db_url(
                self.db_migrator_user,
                self.db_migrator_password,
                self.db_host,
                self.db_port,
                self.db_name,
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
