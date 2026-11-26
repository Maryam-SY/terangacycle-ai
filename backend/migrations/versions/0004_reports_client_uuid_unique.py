"""Unicité de l'Identifiant client par auteur : `reports (owner_key, client_uuid)` (story 1.12).

Rend `POST /v1/reports` idempotent par auteur : un renvoi du même Signalement (même
`owner_key`, même `client_uuid`) ne peut pas créer une seconde ligne, même en parallèle.
La migration n'ajoute que cette contrainte.

Colonnes déclarées dans l'ordre `(client_uuid, owner_key)` : la recherche par le seul
Identifiant client (autre auteur, 409 `client_uuid_conflict`) utilise l'index de la
contrainte. Le nom est celui que `app.modules.reports.repository` reconnaît dans une
violation d'unicité (vérifié par un test).

Revision ID: 0004_reports_client_uuid_unique
Revises: 0003_reports
Create Date: 2026-11-25
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0004_reports_client_uuid_unique"
down_revision: str | Sequence[str] | None = "0003_reports"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CONSTRAINT = "uq_reports_client_uuid_owner_key"
COLUMNS = ("client_uuid", "owner_key")


def upgrade() -> None:
    op.execute(f"ALTER TABLE reports ADD CONSTRAINT {CONSTRAINT} UNIQUE ({', '.join(COLUMNS)})")


def downgrade() -> None:
    op.execute(f"ALTER TABLE reports DROP CONSTRAINT {CONSTRAINT}")
