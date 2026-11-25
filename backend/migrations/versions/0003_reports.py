"""Organisations, appareils, Signalements, photos et Numéros de suivi (story 1.11).

Propriétaires (AD-2) :
  - `orgs` : `organizations`, avec la ligne système de l'Organisation plateforme
    (UUID fixe, `is_demo = false`, sans Zone), responsable de tout Signalement qu'aucune
    commune ni aucun opérateur ne couvre (AD-31) ;
  - `auth` : `devices`, écrite par `auth.service.touch_device()` seulement ;
  - `reports` : `reports`, `report_photos`, `tracking_counters`.

Les valeurs permises des `CHECK` sont celles des énumérations de `app/core/enums.py`
(`OrganizationType`, `OrganizationStatus`, `ReportStatus`, `HeapSize`, `WasteType`),
recopiées ici pour figer la migration ; `tests/integration/test_reports_schema.py`
vérifie qu'elles n'ont pas divergé. `teranga_app` reçoit le DML par les privilèges par
défaut (infra/db/initdb/20-roles.sh).

Revision ID: 0003_reports
Revises: 0002_zones
Create Date: 2026-11-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_reports"
down_revision: str | Sequence[str] | None = "0002_zones"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Organisation plateforme : même valeur que `app.modules.orgs.service.PLATFORM_ORGANIZATION_ID`
# (vérifié par un test).
PLATFORM_ORGANIZATION_ID = "00000000-0000-4000-8000-000000000001"
PLATFORM_ORGANIZATION_NAME = "Plateforme TerangaCycle"

ORGANIZATION_TYPES = (
    "commune",
    "operator",
    "collector_group",
    "enterprise",
    "recycler",
    "platform",
)
ORGANIZATION_STATUSES = ("active", "suspended")
REPORT_STATUSES = ("pending_review", "validated", "assigned", "collected", "rejected")
HEAP_SIZES = ("small", "medium", "large")
WASTE_TYPES = ("plastic", "metal", "glass", "organic", "mixed")
# Commentaire du Citoyen, en caractères (points de code Unicode).
COMMENT_MAX_CHARS = 280

# Tables créées, dans l'ordre des clés étrangères ; le downgrade les supprime à rebours.
TABLES = ("organizations", "devices", "reports", "report_photos", "tracking_counters")


def _in(values: Sequence[str]) -> str:
    return ", ".join(f"'{value}'" for value in values)


def upgrade() -> None:
    op.execute(
        f"""
        CREATE TABLE organizations (
            id uuid NOT NULL,
            type text NOT NULL,
            name text NOT NULL,
            zone_id text,
            status text NOT NULL DEFAULT 'active',
            is_demo boolean NOT NULL DEFAULT false,
            created_at timestamptz NOT NULL,
            updated_at timestamptz NOT NULL,
            CONSTRAINT pk_organizations PRIMARY KEY (id),
            CONSTRAINT fk_organizations_zone_id_zones FOREIGN KEY (zone_id) REFERENCES zones (id),
            CONSTRAINT ck_organizations_type CHECK (type IN ({_in(ORGANIZATION_TYPES)})),
            CONSTRAINT ck_organizations_status CHECK (status IN ({_in(ORGANIZATION_STATUSES)})),
            CONSTRAINT ck_organizations_name_not_blank CHECK (btrim(name) <> ''),
            CONSTRAINT ck_organizations_commune_has_zone
                CHECK (type <> 'commune' OR zone_id IS NOT NULL),
            CONSTRAINT ck_organizations_platform_is_system
                CHECK (type <> 'platform' OR (zone_id IS NULL AND NOT is_demo)),
            CONSTRAINT ck_organizations_platform_is_active
                CHECK (type <> 'platform' OR status = 'active')
        )
        """
    )
    op.execute("CREATE INDEX ix_organizations_zone_id ON organizations (zone_id)")
    # Une seule Organisation plateforme.
    op.execute(
        "CREATE UNIQUE INDEX uq_organizations_platform ON organizations (type) "
        "WHERE type = 'platform'"
    )
    op.execute(
        sa.text(
            """
            INSERT INTO organizations
                (id, type, name, zone_id, status, is_demo, created_at, updated_at)
            VALUES (CAST(:id AS uuid), 'platform', :name, NULL, 'active', false, now(), now())
            """
        ).bindparams(id=PLATFORM_ORGANIZATION_ID, name=PLATFORM_ORGANIZATION_NAME)
    )

    op.execute(
        """
        CREATE TABLE devices (
            device_hash text NOT NULL,
            training_consent boolean NOT NULL,
            consent_at timestamptz NOT NULL,
            first_seen_at timestamptz NOT NULL,
            CONSTRAINT pk_devices PRIMARY KEY (device_hash),
            CONSTRAINT ck_devices_device_hash_hex CHECK (device_hash ~ '^[0-9a-f]{64}$')
        )
        """
    )

    op.execute(
        f"""
        CREATE TABLE reports (
            id uuid NOT NULL,
            tracking_number text NOT NULL,
            owner_key text NOT NULL,
            client_uuid uuid NOT NULL,
            organization_id uuid NOT NULL,
            status text NOT NULL DEFAULT 'pending_review',
            geog geography(Point, 4326) NOT NULL,
            accuracy_m double precision NOT NULL,
            heap_size text NOT NULL,
            comment text,
            citizen_type text,
            zone_id text NOT NULL,
            received_at timestamptz NOT NULL,
            client_captured_at timestamptz NOT NULL,
            flag_imprecise_position boolean NOT NULL DEFAULT false,
            training_consent boolean NOT NULL,
            is_demo boolean NOT NULL DEFAULT false,
            CONSTRAINT pk_reports PRIMARY KEY (id),
            CONSTRAINT uq_reports_tracking_number UNIQUE (tracking_number),
            CONSTRAINT fk_reports_organization_id_organizations
                FOREIGN KEY (organization_id) REFERENCES organizations (id),
            CONSTRAINT fk_reports_zone_id_zones FOREIGN KEY (zone_id) REFERENCES zones (id),
            CONSTRAINT ck_reports_tracking_number
                CHECK (tracking_number ~ '^TC-[0-9]{{4}}-[0-9]{{6}}$'),
            CONSTRAINT ck_reports_owner_key
                CHECK (owner_key ~ '^(device:[0-9a-f]{{64}}|user:[0-9a-f-]{{36}})$'),
            CONSTRAINT ck_reports_status CHECK (status IN ({_in(REPORT_STATUSES)})),
            CONSTRAINT ck_reports_heap_size CHECK (heap_size IN ({_in(HEAP_SIZES)})),
            CONSTRAINT ck_reports_citizen_type CHECK (citizen_type IN ({_in(WASTE_TYPES)})),
            CONSTRAINT ck_reports_comment_length
                CHECK (char_length(comment) <= {COMMENT_MAX_CHARS}),
            CONSTRAINT ck_reports_accuracy_positive
                CHECK (accuracy_m > 0 AND accuracy_m < 'Infinity'::double precision)
        )
        """
    )
    # AD-31 : Organisation responsable indexée ; Zone ; file de modération (Statut, puis
    # ordre de réception) ; Position indexée pour les recherches de proximité (Doublons,
    # story 1.14) ; drapeau indexé (AD-19).
    op.execute("CREATE INDEX ix_reports_organization_id ON reports (organization_id)")
    op.execute("CREATE INDEX ix_reports_zone_id ON reports (zone_id)")
    op.execute("CREATE INDEX ix_reports_status_received_at ON reports (status, received_at)")
    op.execute("CREATE INDEX ix_reports_geog ON reports USING gist (geog)")
    op.execute(
        "CREATE INDEX ix_reports_flag_imprecise_position ON reports (flag_imprecise_position) "
        "WHERE flag_imprecise_position"
    )

    op.execute(
        """
        CREATE TABLE report_photos (
            id uuid NOT NULL,
            report_id uuid NOT NULL,
            object_key text NOT NULL,
            thumb_key text,
            sha256 text NOT NULL,
            width integer NOT NULL,
            height integer NOT NULL,
            created_at timestamptz NOT NULL,
            CONSTRAINT pk_report_photos PRIMARY KEY (id),
            CONSTRAINT fk_report_photos_report_id_reports
                FOREIGN KEY (report_id) REFERENCES reports (id),
            CONSTRAINT uq_report_photos_object_key UNIQUE (object_key),
            CONSTRAINT uq_report_photos_thumb_key UNIQUE (thumb_key),
            CONSTRAINT ck_report_photos_object_key
                CHECK (object_key ~ '^report/[0-9]{4}/[0-9]{2}/[0-9a-f-]{36}\\.jpg$'),
            CONSTRAINT ck_report_photos_sha256_hex CHECK (sha256 ~ '^[0-9a-f]{64}$'),
            CONSTRAINT ck_report_photos_size_positive CHECK (width > 0 AND height > 0)
        )
        """
    )
    op.execute("CREATE INDEX ix_report_photos_report_id ON report_photos (report_id)")
    # Photo identique (story 1.14) : recherche par empreinte des octets reçus (AD-13).
    op.execute("CREATE INDEX ix_report_photos_sha256 ON report_photos (sha256)")

    # Compteur annuel des Numéros de suivi : `INSERT … ON CONFLICT (year) DO UPDATE`.
    op.execute(
        """
        CREATE TABLE tracking_counters (
            year integer NOT NULL,
            n integer NOT NULL,
            CONSTRAINT pk_tracking_counters PRIMARY KEY (year),
            CONSTRAINT ck_tracking_counters_year CHECK (year BETWEEN 2000 AND 9999),
            CONSTRAINT ck_tracking_counters_n CHECK (n BETWEEN 1 AND 999999)
        )
        """
    )


def downgrade() -> None:
    for table in reversed(TABLES):
        op.execute(f"DROP TABLE {table}")
