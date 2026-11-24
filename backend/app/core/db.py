"""Accès à la base : moteur SQLAlchemy et métadonnées communes.

L'unité de travail (AD-17) viendra compléter ce module ; ici, seulement le moteur.
"""

from functools import lru_cache

from sqlalchemy import Engine, MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings

# Convention de nommage des contraintes, pour des migrations Alembic stables.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


@lru_cache
def get_engine() -> Engine:
    """Moteur de l'application, connecté avec le rôle `teranga_app` (DML seulement)."""
    url = get_settings().database_url
    if url is None:
        raise RuntimeError(
            "Base de données non configurée : DATABASE_URL ou le secret db_app_password manque."
        )
    return create_engine(url.get_secret_value(), pool_pre_ping=True)


@lru_cache
def get_sessionmaker() -> sessionmaker:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)
