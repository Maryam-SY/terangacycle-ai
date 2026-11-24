"""Configuration unique de l'application (AD-14, AD-26).

Toute la configuration passe par `Settings` : variables d'environnement pour les
réglages, fichiers de `/run/secrets/` (secrets Compose) pour les secrets.

Une configuration invalide ou un secret manquant refuse le démarrage : voir
`load_settings()` et `load_settings_or_exit()`.
"""

import base64
import json
import logging
import os
import secrets
from functools import lru_cache
from pathlib import Path
from typing import ClassVar

from pydantic import PrivateAttr, SecretStr, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, SettingsError
from sqlalchemy import URL

from app.core.enums import Env
from app.core.logging import configure_logging, get_logger

# Dossier des secrets montés par Compose ; surchargeable pour les tests.
SECRETS_DIR = Path(os.environ.get("SECRETS_DIR", "/run/secrets"))

# Inventaire fixe d'AD-26 : un fichier par secret dans /run/secrets/. En `demo` et en
# `prod`, un fichier absent ou vide bloque le démarrage ; en `dev`, une valeur
# éphémère est générée. Le format des clés n'est pas vérifié ici : chaque story qui
# utilise une clé la valide.
REQUIRED_SECRETS: tuple[str, ...] = (
    "jwt_signing_keys",
    "phone_pepper",
    "device_id_pepper",
    "phone_enc_keys",
    "totp_enc_key",
    "vapid_private_key",
    "s3_access_key_id",
    "s3_secret_access_key",
    "alert_webhook_url",
)

# Marqueurs des valeurs factices (infra/gen-dev-secrets.py, valeurs éphémères de dev) :
# refusées en production.
DEV_SECRET_MARKERS: tuple[str, ...] = (
    "dev-placeholder",
    "dev-ephemeral",
    "alert-disabled",
    "localhost",
)

_log = logging.getLogger(__name__)


class ConfigError(Exception):
    """Configuration refusée ; le message nomme les réglages fautifs, jamais leur valeur."""


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


def _random_b64(size: int = 32) -> str:
    return base64.b64encode(secrets.token_bytes(size)).decode("ascii")


def _ephemeral_secret(name: str) -> str:
    """Valeur de développement au format de l'inventaire d'AD-26 (jamais persistée)."""
    if name == "jwt_signing_keys":
        return json.dumps({f"dev-{secrets.token_hex(4)}": _random_b64()})
    if name == "phone_enc_keys":
        return json.dumps({"dev": _random_b64()})
    if name == "alert_webhook_url":
        return "http://localhost/alert-disabled"
    if name in ("vapid_private_key", "s3_access_key_id", "s3_secret_access_key"):
        return f"dev-ephemeral-{secrets.token_hex(16)}"
    # phone_pepper, device_id_pepper, totp_enc_key : 32 octets en base64.
    return _random_b64()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Sans dossier de secrets (poste de développement), on ne lit que l'environnement.
        secrets_dir=SECRETS_DIR if SECRETS_DIR.is_dir() else None,
        extra="ignore",
        # Les erreurs de validation ne recopient jamais les valeurs reçues (secrets).
        hide_input_in_errors=True,
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

    # Stockage objet Garage (AD-13) : endpoint interne, région, bucket privé.
    s3_endpoint: str = "http://garage:3900"
    s3_region: str = "garage"
    s3_bucket: str = "terangacycle-photos"

    # Version du Modèle livré ; None tant qu'aucun Modèle n'existe (story 3.x).
    model_version: str | None = None

    # Inventaire AD-26 (fichiers de /run/secrets/). Voir REQUIRED_SECRETS.
    jwt_signing_keys: SecretStr | None = None
    phone_pepper: SecretStr | None = None
    device_id_pepper: SecretStr | None = None
    phone_enc_keys: SecretStr | None = None
    totp_enc_key: SecretStr | None = None
    vapid_private_key: SecretStr | None = None
    s3_access_key_id: SecretStr | None = None
    s3_secret_access_key: SecretStr | None = None
    alert_webhook_url: SecretStr | None = None

    # Vérification de l'inventaire AD-26 ; désactivée pour les seules migrations.
    require_secrets: ClassVar[bool] = True

    _ephemeral_secrets: tuple[str, ...] = PrivateAttr(default=())

    @property
    def ephemeral_secrets(self) -> tuple[str, ...]:
        """Secrets générés pour ce processus (ENV=dev seulement)."""
        return self._ephemeral_secrets

    @field_validator("model_version", mode="before")
    @classmethod
    def _empty_model_version_is_none(cls, value: object) -> object:
        # MODEL_VERSION= (vide) dans .env : aucun Modèle livré.
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @model_validator(mode="after")
    def _check_demo_mode(self) -> "Settings":
        # AD-14 : DEMO_MODE interdit en production, exigé par ENV=demo.
        if self.env is Env.PROD and self.demo_mode:
            raise ValueError("DEMO_MODE est interdit quand ENV=prod.")
        if self.env is Env.DEMO and not self.demo_mode:
            raise ValueError("ENV=demo exige DEMO_MODE=true.")
        return self

    @model_validator(mode="after")
    def _check_required_secrets(self) -> "Settings":
        if not self.require_secrets:
            return self
        missing = [name for name in REQUIRED_SECRETS if _is_blank(getattr(self, name))]
        if not missing:
            if self.env is Env.PROD:
                self._check_no_dev_secret()
            return self
        if self.env is not Env.DEV:
            # Le message nomme les secrets, jamais une valeur.
            label = "secret manquant" if len(missing) == 1 else "secrets manquants"
            raise ValueError(f"{label} : {', '.join(missing)}")
        for name in missing:
            setattr(self, name, SecretStr(_ephemeral_secret(name)))
        self._ephemeral_secrets = tuple(missing)
        _log.warning(
            "ENV=dev : secrets éphémères générés pour ce processus : %s", ", ".join(missing)
        )
        return self

    def _check_no_dev_secret(self) -> None:
        # Une valeur factice de développement n'a rien à faire en production.
        rejected = [
            name
            for name in REQUIRED_SECRETS
            if any(
                marker in getattr(self, name).get_secret_value() for marker in DEV_SECRET_MARKERS
            )
        ]
        if rejected:
            raise ValueError(
                "secret de développement refusé en production : " + ", ".join(rejected)
            )

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


class MigratorSettings(Settings):
    """Réglages d'Alembic (service `migrate`) : seule la base est utilisée.

    L'inventaire AD-26 n'y est ni exigé ni monté ; les règles ENV/DEMO_MODE restent.
    """

    require_secrets: ClassVar[bool] = False


def _is_blank(value: SecretStr | None) -> bool:
    return value is None or not value.get_secret_value().strip()


def _describe(exc: ValidationError) -> str:
    """Message lisible, sans aucune valeur reçue (les entrées peuvent être des secrets)."""
    parts = []
    for error in exc.errors(include_url=False, include_input=False, include_context=False):
        message = error["msg"].removeprefix("Value error, ")
        location = ".".join(str(part) for part in error["loc"]).upper()
        parts.append(f"{location} : {message}" if location else message)
    return "configuration invalide : " + " ; ".join(parts)


def load_settings[S: Settings](cls: type[S] = Settings, /, **overrides: object) -> S:
    """Charge les réglages ; lève `ConfigError` (message sans valeur) s'ils sont refusés."""
    try:
        return cls(**overrides)  # type: ignore[arg-type]
    except ValidationError as exc:
        raise ConfigError(_describe(exc)) from None


@lru_cache
def get_settings() -> Settings:
    return load_settings()


def load_settings_or_exit() -> Settings:
    """Pour les points d'entrée (API, worker) : configuration refusée → journal et sortie 1."""
    try:
        return get_settings()
    except (ConfigError, SettingsError, OSError) as exc:
        # Faute de Settings valides, journalisation au niveau par défaut. Hors
        # ConfigError (message déjà sans valeur), seul le type de l'erreur est journalisé.
        reason = str(exc) if isinstance(exc, ConfigError) else type(exc).__name__
        configure_logging()
        get_logger(__name__).critical("startup_refused", reason=reason)
        raise SystemExit(1) from None
