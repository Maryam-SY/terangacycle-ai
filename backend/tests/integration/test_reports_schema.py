"""Schéma de la migration 0003_reports sur PostgreSQL et PostGIS réels (story 1.11).

Exige la pile démarrée et migrée, `TEST_APP_DATABASE_URL` (rôle teranga_app) et
`TEST_MIGRATOR_DATABASE_URL` (rôle teranga_migrator). Sans elles, les tests sont ignorés,
sauf avec `REQUIRE_INTEGRATION=1` (CI) : ils échouent alors.

Le downgrade et l'upgrade sont rejoués dans une transaction annulée : la base partagée
n'est jamais modifiée.
"""

import importlib.util
import os
import re
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from psycopg import errors as pg_errors
from sqlalchemy import Connection, Engine, create_engine, make_url, text
from sqlalchemy.exc import IntegrityError

from app.core.enums import (
    HeapSize,
    OrganizationStatus,
    OrganizationType,
    ReportStatus,
    WasteType,
)
from app.modules.orgs.service import PLATFORM_ORGANIZATION_ID

pytestmark = pytest.mark.integration

MIGRATION = Path(__file__).resolve().parents[2] / "migrations" / "versions" / "0003_reports.py"
TABLES = ("organizations", "devices", "reports", "report_photos", "tracking_counters")
# Contrainte CHECK → énumération de core/enums.py dont elle reprend les valeurs.
ENUM_CHECKS = {
    "ck_organizations_type": OrganizationType,
    "ck_organizations_status": OrganizationStatus,
    "ck_reports_status": ReportStatus,
    "ck_reports_heap_size": HeapSize,
    "ck_reports_citizen_type": WasteType,
}


def _engine(var: str) -> Engine:
    raw = os.environ.get(var)
    if not raw:
        pytest.skip(f"{var} non défini : tests d'intégration ignorés")
    url = make_url(raw)
    if url.drivername in ("postgresql", "postgres"):
        url = url.set(drivername="postgresql+psycopg")
    return create_engine(url, hide_parameters=True)


@pytest.fixture(scope="module")
def app_engine() -> Iterator[Engine]:
    engine = _engine("TEST_APP_DATABASE_URL")
    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def migrator_engine() -> Iterator[Engine]:
    engine = _engine("TEST_MIGRATOR_DATABASE_URL")
    yield engine
    engine.dispose()


@pytest.fixture
def rolled_back(app_engine: Engine) -> Iterator[Connection]:
    """Connexion teranga_app dans une transaction annulée en fin de test."""
    with app_engine.connect() as conn:
        transaction = conn.begin()
        try:
            yield conn
        finally:
            transaction.rollback()


def _migration() -> ModuleType:
    spec = importlib.util.spec_from_file_location("migration_0003_reports", MIGRATION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _exists(conn: Connection, table: str) -> bool:
    return conn.scalar(text("SELECT to_regclass(:t) IS NOT NULL"), {"t": f"public.{table}"})


# --- Organisation plateforme ------------------------------------------------------


def test_platform_organization_row(app_engine: Engine) -> None:
    with app_engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM organizations WHERE type = 'platform'")
        ).one()  # une seule
    assert row.id == PLATFORM_ORGANIZATION_ID
    assert (row.status, row.is_demo, row.zone_id) == ("active", False, None)
    assert row.name.strip()


@pytest.mark.parametrize(
    ("statement", "constraint"),
    [
        (
            "INSERT INTO organizations (id, type, name, created_at, updated_at) "
            "VALUES (gen_random_uuid(), 'commune', 'Commune sans Zone', now(), now())",
            "ck_organizations_commune_has_zone",
        ),
        (
            "INSERT INTO organizations (id, type, name, created_at, updated_at) "
            "VALUES (gen_random_uuid(), 'platform', 'Seconde plateforme', now(), now())",
            "uq_organizations_platform",
        ),
        (
            "UPDATE organizations SET is_demo = true WHERE type = 'platform'",
            "ck_organizations_platform_is_system",
        ),
        (
            "INSERT INTO organizations (id, type, name, zone_id, status, created_at, updated_at) "
            "VALUES (gen_random_uuid(), 'commune', 'X', 'dakar', 'closed', now(), now())",
            "ck_organizations_status",
        ),
    ],
    ids=["commune-sans-zone", "seconde-plateforme", "plateforme-demo", "statut-inconnu"],
)
def test_organization_constraints(rolled_back: Connection, statement: str, constraint: str) -> None:
    with pytest.raises(IntegrityError) as exc_info, rolled_back.begin_nested():
        rolled_back.execute(text(statement))
    assert isinstance(exc_info.value.orig, pg_errors.IntegrityError)
    assert exc_info.value.orig.diag.constraint_name == constraint


# --- Colonnes, contraintes et index ------------------------------------------------


def test_check_constraints_use_core_enums(app_engine: Engine) -> None:
    with app_engine.connect() as conn:
        definitions = dict(
            conn.execute(
                text(
                    "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint "
                    "WHERE conname = ANY(:names)"
                ),
                {"names": list(ENUM_CHECKS)},
            ).all()
        )
    assert set(definitions) == set(ENUM_CHECKS)
    for name, enum in ENUM_CHECKS.items():
        values = set(re.findall(r"'([a-z_]+)'::text", definitions[name]))
        assert values == {member.value for member in enum}, name


def test_report_columns(app_engine: Engine) -> None:
    with app_engine.connect() as conn:
        columns = {
            (row.table_name, row.column_name): row
            for row in conn.execute(
                text(
                    "SELECT table_name, column_name, is_nullable, column_default, data_type, "
                    "udt_name FROM information_schema.columns WHERE table_name = ANY(:t)"
                ),
                {"t": list(TABLES)},
            )
        }

    def nullable(table: str, column: str) -> bool:
        return columns[(table, column)].is_nullable == "YES"

    assert not nullable("reports", "organization_id")
    assert not nullable("reports", "is_demo")
    assert columns[("reports", "is_demo")].column_default == "false"
    assert columns[("reports", "status")].column_default == "'pending_review'::text"
    assert columns[("reports", "geog")].udt_name == "geography"
    assert nullable("reports", "citizen_type") and nullable("reports", "comment")
    assert nullable("report_photos", "thumb_key")
    assert not nullable("organizations", "is_demo")
    assert nullable("organizations", "zone_id")
    for column in ("device_hash", "training_consent", "consent_at", "first_seen_at"):
        assert not nullable("devices", column), column


def test_comment_check_counts_characters(app_engine: Engine) -> None:
    with app_engine.connect() as conn:
        definition = conn.scalar(
            text(
                "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE conname = 'ck_reports_comment_length'"
            )
        )
    assert definition == "CHECK ((char_length(comment) <= 280))"


def test_organization_foreign_key_has_no_on_delete_and_is_indexed(app_engine: Engine) -> None:
    with app_engine.connect() as conn:
        fk = conn.execute(
            text(
                "SELECT confrelid::regclass::text AS target, confdeltype, confupdtype "
                "FROM pg_constraint WHERE conname = 'fk_reports_organization_id_organizations'"
            )
        ).one()
        indexes = conn.scalars(
            text("SELECT indexdef FROM pg_indexes WHERE tablename = 'reports'")
        ).all()
    # `a` : NO ACTION, ni CASCADE ni SET NULL (AD-21, AD-31).
    assert (fk.target, fk.confdeltype, fk.confupdtype) == ("organizations", "a", "a")
    assert any("(organization_id)" in index for index in indexes), indexes
    assert any("gist (geog)" in index for index in indexes), indexes


def test_app_role_has_dml_on_the_new_tables(app_engine: Engine) -> None:
    with app_engine.connect() as conn:
        for table in TABLES:
            for privilege in ("SELECT", "INSERT", "UPDATE", "DELETE"):
                assert conn.scalar(
                    text("SELECT has_table_privilege('teranga_app', :t, :p)"),
                    {"t": table, "p": privilege},
                ), (table, privilege)
            # Le schéma reste au migrateur.
            assert not conn.scalar(
                text("SELECT has_table_privilege('teranga_app', :t, 'TRUNCATE')"), {"t": table}
            )


# --- Downgrade et upgrade, dans une transaction annulée ----------------------------


def test_downgrade_drops_the_tables_and_upgrade_recreates_them(migrator_engine: Engine) -> None:
    migration = _migration()
    with migrator_engine.connect() as conn:
        transaction = conn.begin()
        try:
            # Délai borné : un verrou tenu ailleurs fait échouer le test, sans l'attendre.
            conn.execute(text("SET LOCAL lock_timeout = '5s'"))
            with Operations.context(MigrationContext.configure(conn)):
                migration.downgrade()
                assert not any(_exists(conn, table) for table in TABLES)
                assert _exists(conn, "zones")
                migration.upgrade()
            assert all(_exists(conn, table) for table in TABLES)
            platform = conn.execute(text("SELECT id, type, is_demo FROM organizations")).one()
            assert (platform.id, platform.type, platform.is_demo) == (
                PLATFORM_ORGANIZATION_ID,
                "platform",
                False,
            )
        finally:
            transaction.rollback()
