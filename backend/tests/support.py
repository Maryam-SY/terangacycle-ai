"""Outils partagés des tests."""

from app.core.geo import ActiveZone, MultiPolygon


def fake_secret_value(name: str) -> str:
    """Valeur factice reconnaissable, propre à chaque secret de l'inventaire."""
    return f"fake-{name}-Vq7"


def sample_active_zone() -> ActiveZone:
    """Zone active factice (un carré autour de Dakar) : les tests unitaires ne lancent pas
    le lifespan qui la lit en base, ils la posent dans `app.state.active_zone`."""
    square = [[-17.55, 14.65], [-17.40, 14.65], [-17.40, 14.80], [-17.55, 14.80], [-17.55, 14.65]]
    return ActiveZone(
        id="dakar",
        name="Dakar",
        geometry=MultiPolygon(type="MultiPolygon", coordinates=[[square]]),
    )
