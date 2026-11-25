"""Étiquette « Données de démonstration » (AD-14, story 1.11).

Toute ligne métier porte `is_demo`, calculé ici et nulle part ailleurs : vrai en Mode
démonstration (`DEMO_MODE`, interdit en production), ou si son parent est lui-même
étiqueté.
"""

from app.core.config import get_settings


def flag(parent_is_demo: bool = False) -> bool:
    """Valeur de `is_demo` pour une ligne créée maintenant."""
    return get_settings().demo_mode or parent_is_demo
