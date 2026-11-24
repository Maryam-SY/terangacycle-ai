"""Rôles PostgreSQL et PostGIS (story 1.1, AD-15).

Exige la pile démarrée et deux URL de connexion :
`TEST_APP_DATABASE_URL` (rôle teranga_app) et `TEST_MIGRATOR_DATABASE_URL`
(rôle teranga_migrator). Sans elles, les tests sont ignorés, sauf avec
`REQUIRE_INTEGRATION=1` (CI) : ils échouent alors (`tests/conftest.py`).
"""

import os
import uuid
from collections.abc import Iterator

import pytest
from psycopg import errors as pg_errors
from sqlalchemy import Engine, create_engine, make_url, text
from sqlalchemy.exc import ProgrammingError

pytestmark = pytest.mark.integration


def _engine_from_env(var: str) -> Engine:
    raw = os.environ.get(var)
    if not raw:
        pytest.skip(f"{var} non défini : tests d'intégration ignorés")
    url = make_url(raw)
    if url.drivername in ("postgresql", "postgres"):
        url = url.set(drivername="postgresql+psycopg")
    return create_engine(url)


@pytest.fixture(scope="module")
def app_engine() -> Iterator[Engine]:
    engine = _engine_from_env("TEST_APP_DATABASE_URL")
    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def migrator_engine() -> Iterator[Engine]:
    engine = _engine_from_env("TEST_MIGRATOR_DATABASE_URL")
    yield engine
    engine.dispose()


def _table_name() -> str:
    return f"tmp_roles_{uuid.uuid4().hex[:12]}"


def test_connections_use_expected_roles(app_engine: Engine, migrator_engine: Engine) -> None:
    with app_engine.connect() as conn:
        assert conn.scalar(text("SELECT current_user")) == "teranga_app"
    with migrator_engine.connect() as conn:
        assert conn.scalar(text("SELECT current_user")) == "teranga_migrator"


def test_app_role_cannot_create_table(app_engine: Engine) -> None:
    with app_engine.connect() as conn, pytest.raises(ProgrammingError) as exc_info:
        conn.execute(text(f"CREATE TABLE {_table_name()} (id int)"))
    assert isinstance(exc_info.value.orig, pg_errors.InsufficientPrivilege)


def test_migrator_role_can_create_table(migrator_engine: Engine) -> None:
    name = _table_name()
    with migrator_engine.connect() as conn:
        trans = conn.begin()
        conn.execute(text(f"CREATE TABLE {name} (id int)"))
        owner = conn.scalar(
            text("SELECT tableowner FROM pg_tables WHERE schemaname = 'public' AND tablename = :t"),
            {"t": name},
        )
        trans.rollback()
    assert owner == "teranga_migrator"


def test_migrator_owns_public_schema(migrator_engine: Engine) -> None:
    with migrator_engine.connect() as conn:
        owner = conn.scalar(
            text("SELECT pg_get_userbyid(nspowner) FROM pg_namespace WHERE nspname = 'public'")
        )
    assert owner == "teranga_migrator"


def test_app_role_gets_dml_on_future_tables(app_engine: Engine, migrator_engine: Engine) -> None:
    """Les DEFAULT PRIVILEGES donnent le DML à teranga_app, sans le droit de modifier le schéma."""
    name = _table_name()
    with migrator_engine.begin() as conn:
        conn.execute(text(f"CREATE TABLE {name} (id serial PRIMARY KEY, label text)"))
    try:
        with app_engine.begin() as conn:
            conn.execute(text(f"INSERT INTO {name} (label) VALUES ('a')"))
            conn.execute(text(f"UPDATE {name} SET label = 'b'"))
            assert conn.scalar(text(f"SELECT label FROM {name}")) == "b"
            conn.execute(text(f"DELETE FROM {name}"))
        with app_engine.connect() as conn, pytest.raises(ProgrammingError) as exc_info:
            conn.execute(text(f"ALTER TABLE {name} ADD COLUMN extra int"))
        # Seul le propriétaire peut modifier la table.
        assert isinstance(exc_info.value.orig, pg_errors.InsufficientPrivilege)
    finally:
        with migrator_engine.begin() as conn:
            conn.execute(text(f"DROP TABLE IF EXISTS {name}"))


def test_postgis_extension_is_active(app_engine: Engine) -> None:
    with app_engine.connect() as conn:
        installed = conn.scalar(text("SELECT 1 FROM pg_extension WHERE extname = 'postgis'"))
        version = conn.scalar(text("SELECT postgis_lib_version()"))
    assert installed == 1
    assert version.startswith("3.")
