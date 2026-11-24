"""Environnement Alembic : seul chemin de modification du schéma (AD-15).

Les migrations s'exécutent avec le rôle `teranga_migrator`, propriétaire du schéma
`public`, via `MIGRATOR_DATABASE_URL` (ou le secret `db_migrator_password`).
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.core.config import MigratorSettings, load_settings
from app.core.db import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _migrator_url() -> str:
    # Réglages de migration : l'inventaire AD-26 de l'API n'est pas exigé ici.
    url = load_settings(MigratorSettings).migrator_database_url
    if url is None:
        raise RuntimeError(
            "MIGRATOR_DATABASE_URL ou le secret db_migrator_password manque : migration impossible."
        )
    return url.get_secret_value()


def run_migrations_offline() -> None:
    context.configure(
        url=_migrator_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_migrator_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
