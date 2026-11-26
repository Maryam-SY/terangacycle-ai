"""Étiquette « Données de démonstration » (AD-14, FR-37).

`DEMO_MODE` est la seule source du Mode démonstration. Tout ce qui est créé pendant ce
mode porte `is_demo = true`, comme tout enfant d'une donnée de démonstration.
"""

from app.core.config import Settings, get_settings


def flag(parent_is_demo: bool = False, *, settings: Settings | None = None) -> bool:
    """Valeur de `is_demo` d'une nouvelle ligne : Mode démonstration ou parent étiqueté."""
    settings = settings or get_settings()
    return settings.demo_mode or parent_is_demo
