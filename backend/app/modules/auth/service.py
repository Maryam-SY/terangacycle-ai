"""Service du module `auth` : appareils des Citoyens anonymes (AD-9, AD-24).

`devices` n'est écrite que par `touch_device()`, appelée par `reports.service.create()`.
"""

from datetime import datetime

from app.core.db import transactional
from app.modules.auth import repository


@transactional
def touch_device(device_hash: str, training_consent: bool, now: datetime) -> None:
    """Crée la ligne de l'appareil, ou met à jour son choix de réentraînement.

    `first_seen_at` ne change jamais ; `consent_at` change seulement avec le choix.
    """
    repository.upsert_device(device_hash, training_consent, now)
