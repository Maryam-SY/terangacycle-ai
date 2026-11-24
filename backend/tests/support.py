"""Outils partagés des tests."""


def fake_secret_value(name: str) -> str:
    """Valeur factice reconnaissable, propre à chaque secret de l'inventaire."""
    return f"fake-{name}-Vq7"
