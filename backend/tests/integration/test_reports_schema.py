"""Schéma des migrations 0003_reports (story 1.11) et 0004_reports_client_uuid_unique
(story 1.12) sur PostgreSQL et PostGIS réels.

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
from app.modules.reports.repository import CLIENT_UUID_CONSTRAINT

pytestmark = pytest.mark.integration

VERSIONS = Path(__file__).resolve().parents[2] / "migrations" / "versions"
MIGRATION = VERSIONS / "0003_reports.py"
MIGRATION_0004 = VERSIONS / "0004_reports_client_uuid_unique.py"
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


def _migration(path: Path = MIGRATION, name: str = "migration_0003_reports") -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
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
            "UPDATE organizations SET status = 'suspended' WHERE type = 'platform'",
            "ck_organizations_platform_is_active",
        ),
        (
            "INSERT INTO organizations (id, type, name, zone_id, status, created_at, updated_at) "
            "VALUES (gen_random_uuid(), 'commune', 'X', 'dakar', 'closed', now(), now())",
            "ck_organizations_status",
        ),
    ],
    ids=[
        "commune-sans-zone",
        "seconde-plateforme",
        "plateforme-demo",
        "plateforme-suspendue",
        "statut-inconnu",
    ],
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
        indexes = dict(
            conn.execute(
                text("SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'reports'")
            ).all()
        )
    # `a` : NO ACTION, ni CASCADE ni SET NULL (AD-21, AD-31).
    assert (fk.target, fk.confdeltype, fk.confupdtype) == ("organizations", "a", "a")
    expected = {
        "ix_reports_organization_id": "(organization_id)",
        "ix_reports_zone_id": "(zone_id)",
        # File de modération : par Statut, puis dans l'ordre de réception.
        "ix_reports_status_received_at": "(status, received_at)",
        "ix_reports_geog": "gist (geog)",
    }
    for name, columns in expected.items():
        assert columns in indexes.get(name, ""), (name, indexes)


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


# --- Migration 0004 : unicité de l'Identifiant client par auteur (story 1.12) ----------


def _schema_objects(conn: Connection) -> set[tuple[str, str, str]]:
    """Contraintes et index du schéma `public` : (table, nom, définition)."""
    constraints = conn.execute(
        text(
            "SELECT conrelid::regclass::text, conname, pg_get_constraintdef(oid) "
            "FROM pg_constraint WHERE connamespace = 'public'::regnamespace"
        )
    ).all()
    indexes = conn.execute(
        text("SELECT tablename, indexname, indexdef FROM pg_indexes WHERE schemaname = 'public'")
    ).all()
    return {tuple(row) for row in (*constraints, *indexes)}


def _columns(conn: Connection) -> set[tuple[str, str, str]]:
    return {
        tuple(row)
        for row in conn.execute(
            text(
                "SELECT table_name, column_name, data_type FROM information_schema.columns "
                "WHERE table_schema = 'public'"
            )
        )
    }


def test_client_uuid_unique_constraint_and_column_order(app_engine: Engine) -> None:
    with app_engine.connect() as conn:
        constraint = conn.execute(
            text(
                "SELECT contype, conrelid::regclass::text AS tbl, "
                "pg_get_constraintdef(oid) AS definition FROM pg_constraint WHERE conname = :name"
            ),
            {"name": CLIENT_UUID_CONSTRAINT},
        ).one()
        index = conn.scalar(
            text("SELECT indexdef FROM pg_indexes WHERE indexname = :name"),
            {"name": CLIENT_UUID_CONSTRAINT},
        )
    # Colonnes {owner_key, client_uuid}, déclarées `client_uuid` d'abord : la recherche par
    # seul Identifiant client (409) utilise l'index.
    assert (constraint.contype, constraint.tbl) == ("u", "reports")
    assert constraint.definition == "UNIQUE (client_uuid, owner_key)"
    assert index.endswith("USING btree (client_uuid, owner_key)"), index


def test_same_client_uuid_is_refused_for_one_owner_only(rolled_back: Connection) -> None:
    owner = "device:" + "a" * 64
    client_uuid = "6f1c2a4e-1b2c-4d3e-8f90-a1b2c3d4e5f6"
    insert = text(
        """
        INSERT INTO reports (
            id, tracking_number, owner_key, client_uuid, organization_id, geog, accuracy_m,
            heap_size, zone_id, received_at, client_captured_at, training_consent
        ) VALUES (
            gen_random_uuid(), :number, :owner, CAST(:client_uuid AS uuid),
            CAST(:org AS uuid), ST_GeogFromText('POINT(-17.4381 14.6708)'), 10, 'small',
            'dakar', now(), now(), false
        )
        """
    )
    params = {"owner": owner, "client_uuid": client_uuid, "org": str(PLATFORM_ORGANIZATION_ID)}
    rolled_back.execute(insert, {**params, "number": "TC-9999-999998"})
    # Autre auteur, même Identifiant client : accepté par la base (le 409 vient du service).
    rolled_back.execute(
        insert, {**params, "number": "TC-9999-999997", "owner": "device:" + "b" * 64}
    )
    with pytest.raises(IntegrityError) as exc_info, rolled_back.begin_nested():
        rolled_back.execute(insert, {**params, "number": "TC-9999-999999"})
    assert exc_info.value.orig.diag.constraint_name == CLIENT_UUID_CONSTRAINT


def test_migration_0004_adds_only_the_constraint(migrator_engine: Engine) -> None:
    migration = _migration(MIGRATION_0004, "migration_0004_reports_client_uuid_unique")
    assert migration.CONSTRAINT == CLIENT_UUID_CONSTRAINT
    with migrator_engine.connect() as conn:
        transaction = conn.begin()
        try:
            conn.execute(text("SET LOCAL lock_timeout = '5s'"))
            with_constraint = _schema_objects(conn)
            columns = _columns(conn)
            with Operations.context(MigrationContext.configure(conn)):
                migration.downgrade()
                without = _schema_objects(conn)
                assert {name for _, name, _ in with_constraint - without} == {
                    CLIENT_UUID_CONSTRAINT
                }
                assert without < with_constraint
                assert _columns(conn) == columns
                migration.upgrade()
            assert _schema_objects(conn) == with_constraint
            assert _columns(conn) == columns
        finally:
            transaction.rollback()
