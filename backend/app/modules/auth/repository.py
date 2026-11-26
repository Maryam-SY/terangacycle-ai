"""Accès à la table `devices` (propriété du module `auth`, AD-2)."""

from datetime import datetime

from sqlalchemy import text

from app.core.db import current_session

_UPSERT_DEVICE = text(
    """
    INSERT INTO devices (device_hash, training_consent, consent_at, first_seen_at)
    VALUES (:device_hash, :training_consent, :now, :now)
    ON CONFLICT (device_hash) DO UPDATE SET
        training_consent = EXCLUDED.training_consent,
        -- La date du choix ne change que si le choix change.
        consent_at = CASE
            WHEN devices.training_consent IS DISTINCT FROM EXCLUDED.training_consent
            THEN EXCLUDED.consent_at
            ELSE devices.consent_at
        END
    """
)


def upsert_device(device_hash: str, training_consent: bool, now: datetime) -> None:
    current_session().execute(
        _UPSERT_DEVICE,
        {"device_hash": device_hash, "training_consent": training_consent, "now": now},
    )
