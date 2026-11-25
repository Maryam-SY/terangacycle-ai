"""Service du module auth (AD-9, AD-24).

`touch_device()` est la seule écriture de `devices` : elle crée la ligne d'un appareil vu
pour la première fois, ou y reporte le choix courant du réentraînement.
"""

from datetime import datetime

from app.core.db import transactional
from app.modules.auth import repository


@transactional
def touch_device(device_hash: str, *, training_consent: bool, seen_at: datetime) -> None:
    """Crée ou met à jour l'appareil `device_hash` (empreinte, jamais l'Identifiant)."""
    repository.upsert_device(device_hash, training_consent, seen_at)
