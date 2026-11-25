"""Accès aux tables `reports`, `report_photos` et `tracking_counters` (propriété de
`reports`, AD-2). Aucun contrôle de transaction ici (AD-17)."""

from dataclasses import asdict, dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import text

from app.core.db import current_session

# Compteur annuel (AD-18) : la ligne de l'année est verrouillée jusqu'au commit, deux
# créations simultanées obtiennent donc deux valeurs distinctes.
_NEXT_TRACKING_SEQUENCE = text(
    """
    INSERT INTO tracking_counters (year, n) VALUES (:year, 1)
    ON CONFLICT (year) DO UPDATE SET n = tracking_counters.n + 1
    RETURNING n
    """
)

_INSERT_REPORT = text(
    """
    INSERT INTO reports (
        id, tracking_number, owner_key, client_uuid, organization_id, status, geog,
        accuracy_m, heap_size, comment, citizen_type, zone_id, received_at,
        client_captured_at, flag_imprecise_position, training_consent, is_demo
    ) VALUES (
        :id, :tracking_number, :owner_key, :client_uuid, :organization_id, :status,
        ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
        :accuracy_m, :heap_size, :comment, :citizen_type, :zone_id, :received_at,
        :client_captured_at, :flag_imprecise_position, :training_consent, :is_demo
    )
    """
)

_INSERT_PHOTO = text(
    """
    INSERT INTO report_photos (id, report_id, object_key, sha256, width, height, created_at)
    VALUES (:id, :report_id, :object_key, :sha256, :width, :height, :created_at)
    """
)


@dataclass(frozen=True, slots=True)
class NewReport:
    id: UUID
    tracking_number: str
    owner_key: str
    client_uuid: UUID
    organization_id: UUID
    status: str
    lat: float
    lng: float
    accuracy_m: float
    heap_size: str
    comment: str | None
    citizen_type: str | None
    zone_id: str
    received_at: datetime
    client_captured_at: datetime
    flag_imprecise_position: bool
    training_consent: bool
    is_demo: bool


@dataclass(frozen=True, slots=True)
class NewPhoto:
    id: UUID
    report_id: UUID
    object_key: str
    sha256: str
    width: int
    height: int
    created_at: datetime


def next_tracking_sequence(year: int) -> int:
    """Rang suivant de l'année dans le compteur des Numéros de suivi (1 pour le premier)."""
    return current_session().execute(_NEXT_TRACKING_SEQUENCE, {"year": year}).scalar_one()


def insert_report(report: NewReport) -> None:
    current_session().execute(_INSERT_REPORT, asdict(report))


def insert_photo(photo: NewPhoto) -> None:
    current_session().execute(_INSERT_PHOTO, asdict(photo))
