"""Étiquette « Données de démonstration » (AD-14, story 1.11).

Toute ligne métier porte `is_demo`, calculé ici et nulle part ailleurs : vrai en Mode
démonstration (`DEMO_MODE`, interdit en production), ou si son parent est lui-même
étiqueté. Les réglages sont ceux avec lesquels l'application a été construite.
"""

from app.core.config import Settings


def flag(settings: Settings, parent_is_demo: bool = False) -> bool:
    """Valeur de `is_demo` pour une ligne créée maintenant."""
    return settings.demo_mode or parent_is_demo
