"""Unicité de l'Identifiant client par auteur : `reports (owner_key, client_uuid)` (story 1.12).

Rend `POST /v1/reports` idempotent par auteur : un renvoi du même Signalement (même
`owner_key`, même `client_uuid`) ne peut pas créer une seconde ligne, même en parallèle.
La migration n'ajoute que cette contrainte. Des paires `(client_uuid, owner_key)` déjà en
double (envois répétés reçus par la story 1.11) la font refuser avec un message clair : leur
nombre et le remède ; aucun dédoublonnage automatique.

Colonnes déclarées dans l'ordre `(client_uuid, owner_key)` : la recherche par le seul
Identifiant client (autre auteur, 409 `client_uuid_conflict`) utilise l'index de la
contrainte. Le nom est celui que `app.modules.reports.repository` reconnaît dans une
violation d'unicité (vérifié par un test).

Revision ID: 0004_reports_client_uuid_unique
Revises: 0003_reports
Create Date: 2026-11-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_reports_client_uuid_unique"
down_revision: str | Sequence[str] | None = "0003_reports"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CONSTRAINT = "uq_reports_client_uuid_owner_key"
COLUMNS = ("client_uuid", "owner_key")

_DUPLICATE_PAIRS = sa.text(
    """
    SELECT count(*) FROM (
        SELECT 1 FROM reports GROUP BY client_uuid, owner_key HAVING count(*) > 1
    ) AS duplicates
    """
)


class DuplicateClientUuidError(RuntimeError):
    """Paires `(client_uuid, owner_key)` en double : la contrainte ne peut pas être posée."""


def _refuse_duplicates() -> None:
    if op.get_context().as_sql:
        return  # mode hors ligne : aucune base à lire
    duplicates = op.get_bind().execute(_DUPLICATE_PAIRS).scalar_one()
    if duplicates:
        raise DuplicateClientUuidError(
            f"{CONSTRAINT} impossible : {duplicates} paire(s) (client_uuid, owner_key) en "
            "double dans reports. Remède : retirer à la main les Signalements en trop de chaque "
            "paire (garder le premier reçu, avec ses photos et objets), puis relancer la "
            "migration. Aucun dédoublonnage automatique."
        )


def upgrade() -> None:
    _refuse_duplicates()
    op.execute(f"ALTER TABLE reports ADD CONSTRAINT {CONSTRAINT} UNIQUE ({', '.join(COLUMNS)})")


def downgrade() -> None:
    op.execute(f"ALTER TABLE reports DROP CONSTRAINT {CONSTRAINT}")
