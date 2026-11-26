"""Note vocale facultative d'un Signalement (story 1.13).

Le Citoyen qui ne lit ni n'écrit peut décrire le dépôt à voix haute (en wolof ou en
français) au lieu d'écrire un commentaire. La note est rangée dans le bucket privé ;
`reports.voice_key` garde sa clé.

Revision ID: 0004_report_voice
Revises: 0003_reports
Create Date: 2026-11-26
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0004_report_voice"
down_revision: str | Sequence[str] | None = "0003_reports"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE reports ADD COLUMN voice_key text")
    op.execute("ALTER TABLE reports ADD CONSTRAINT uq_reports_voice_key UNIQUE (voice_key)")


def downgrade() -> None:
    op.execute("ALTER TABLE reports DROP COLUMN voice_key")
