"""Outils partagés des tests."""

import base64

from app.core.geo import ActiveZone, MultiPolygon

# Secrets de l'inventaire d'AD-26 au format « 32 octets en base64 », vérifié au démarrage
# pour DEVICE_ID_PEPPER (story 1.11).
BASE64_32_SECRETS = frozenset({"phone_pepper", "device_id_pepper", "totp_enc_key"})


def fake_secret_value(name: str) -> str:
    """Valeur factice reconnaissable, propre à chaque secret de l'inventaire ; au format
    attendu (32 octets en base64) pour les peppers et clés de 32 octets."""
    value = f"fake-{name}-Vq7"
    if name in BASE64_32_SECRETS:
        return base64.b64encode(value.encode().ljust(32, b".")).decode("ascii")
    return value


def sample_active_zone() -> ActiveZone:
    """Zone active factice (un carré autour de Dakar) : les tests unitaires ne lancent pas
    le lifespan qui la lit en base, ils la posent dans `app.state.active_zone`."""
    square = [[-17.55, 14.65], [-17.40, 14.65], [-17.40, 14.80], [-17.55, 14.80], [-17.55, 14.65]]
    return ActiveZone(
        id="dakar",
        name="Dakar",
        geometry=MultiPolygon(type="MultiPolygon", coordinates=[[square]]),
    )
