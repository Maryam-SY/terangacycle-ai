"""Signalements anonymes : `devices`, `reports`, `report_photos`, `tracking_counters`
(story 1.11).

Propriétaires (AD-2) : `auth` possède `devices` ; `reports` possède les trois autres.
`teranga_app` reçoit le DML par les privilèges par défaut (infra/db/initdb/20-roles.sh).

Les valeurs des CHECK viennent de `app.core.enums` (énumérations uniques de l'épine).
L'unicité `(owner_key, client_uuid)` arrive avec la story 1.12. La colonne
`report_photos.thumb_key` est créée ici, nulle ; la story de la miniature la renseigne.

Revision ID: 0003_reports
Revises: 0002_zones
Create Date: 2026-11-26
"""

from collections.abc import Sequence
from enum import StrEnum

from alembic import op

from app.core.enums import PileSize, ReportStatus, WasteType

revision: str = "0003_reports"
down_revision: str | Sequence[str] | None = "0002_zones"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _values(enum: type[StrEnum]) -> str:
    """Liste SQL `'a', 'b'` des valeurs d'une énumération (codes ASCII de l'épine)."""
    return ", ".join(f"'{member.value}'" for member in enum)


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE devices (
            device_hash text PRIMARY KEY,
            training_consent boolean NOT NULL,
            consent_at timestamptz NOT NULL,
            first_seen_at timestamptz NOT NULL,
            CONSTRAINT ck_devices_device_hash CHECK (device_hash ~ '^[0-9a-f]{64}$')
        )
        """
    )
    op.execute(
        """
        CREATE TABLE tracking_counters (
            year integer PRIMARY KEY,
            n integer NOT NULL,
            CONSTRAINT ck_tracking_counters_year CHECK (year BETWEEN 2000 AND 9999),
            CONSTRAINT ck_tracking_counters_n CHECK (n BETWEEN 1 AND 999999)
        )
        """
    )
    op.execute(
        f"""
        CREATE TABLE reports (
            id uuid PRIMARY KEY,
            tracking_number text NOT NULL,
            owner_key text NOT NULL,
            client_uuid uuid NOT NULL,
            geog geography(Point, 4326) NOT NULL,
            accuracy_m double precision NOT NULL,
            client_captured_at timestamptz NOT NULL,
            pile_size text NOT NULL,
            comment text,
            citizen_type text,
            zone_id text NOT NULL REFERENCES zones (id),
            status text NOT NULL DEFAULT '{ReportStatus.PENDING_REVIEW.value}',
            received_at timestamptz NOT NULL,
            training_consent boolean NOT NULL,
            is_demo boolean NOT NULL DEFAULT false,
            flag_imprecise_position boolean NOT NULL DEFAULT false,
            CONSTRAINT uq_reports_tracking_number UNIQUE (tracking_number),
            CONSTRAINT ck_reports_tracking_number
                CHECK (tracking_number ~ '^TC-[0-9]{{4}}-[0-9]{{6}}$'),
            CONSTRAINT ck_reports_owner_key CHECK (owner_key ~ '^(device|user):.+$'),
            CONSTRAINT ck_reports_accuracy_m CHECK (accuracy_m > 0),
            CONSTRAINT ck_reports_pile_size CHECK (pile_size IN ({_values(PileSize)})),
            CONSTRAINT ck_reports_comment CHECK (char_length(comment) <= 280),
            CONSTRAINT ck_reports_citizen_type
                CHECK (citizen_type IS NULL OR citizen_type IN ({_values(WasteType)})),
            CONSTRAINT ck_reports_status CHECK (status IN ({_values(ReportStatus)}))
        )
        """  # noqa: S608 - valeurs des énumérations de l'épine, pas d'entrée utilisateur
    )
    op.execute("CREATE INDEX ix_reports_geog ON reports USING gist (geog)")
    op.execute("CREATE INDEX ix_reports_owner_key ON reports (owner_key)")
    op.execute("CREATE INDEX ix_reports_zone_id ON reports (zone_id)")
    op.execute("CREATE INDEX ix_reports_status ON reports (status)")
    op.execute(
        """
        CREATE TABLE report_photos (
            id uuid PRIMARY KEY,
            report_id uuid NOT NULL REFERENCES reports (id) ON DELETE CASCADE,
            object_key text NOT NULL,
            thumb_key text,
            sha256 text NOT NULL,
            width integer NOT NULL,
            height integer NOT NULL,
            created_at timestamptz NOT NULL,
            CONSTRAINT uq_report_photos_object_key UNIQUE (object_key),
            CONSTRAINT uq_report_photos_thumb_key UNIQUE (thumb_key),
            CONSTRAINT ck_report_photos_sha256 CHECK (sha256 ~ '^[0-9a-f]{64}$'),
            CONSTRAINT ck_report_photos_size CHECK (width > 0 AND height > 0)
        )
        """
    )
    op.execute("CREATE INDEX ix_report_photos_report_id ON report_photos (report_id)")
    op.execute("CREATE INDEX ix_report_photos_sha256 ON report_photos (sha256)")


def downgrade() -> None:
    op.execute("DROP TABLE report_photos")
    op.execute("DROP TABLE reports")
    op.execute("DROP TABLE tracking_counters")
    op.execute("DROP TABLE devices")
