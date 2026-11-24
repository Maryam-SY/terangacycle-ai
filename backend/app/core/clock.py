"""Horloge unique du serveur (AD-18).

Tout « maintenant » vient de `now()` ; jamais `datetime.now()` ni `NOW()` pour une
règle métier. Les tests remplacent `now` pour simuler le temps.
"""

from datetime import UTC, datetime


def now() -> datetime:
    """Instant présent, en UTC, avec fuseau."""
    return datetime.now(UTC)
