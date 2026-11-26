"""Accès aux tables du module `reports` : `reports`, `report_photos`, `tracking_counters`.

Aucune transaction ici : la session est celle de l'unité de travail en cours (AD-17).
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import text

from app.core.db import current_session

_NEXT_TRACKING_N = text(
    """
    INSERT INTO tracking_counters (year, n) VALUES (:year, 1)
    ON CONFLICT (year) DO UPDATE SET n = tracking_counters.n + 1
    RETURNING n
    """
)

_INSERT_REPORT = text(
    """
    INSERT INTO reports (
        id, tracking_number, owner_key, client_uuid, geog, accuracy_m, client_captured_at,
        pile_size, comment, citizen_type, zone_id, status, received_at, training_consent,
        is_demo, flag_imprecise_position
    ) VALUES (
        :id, :tracking_number, :owner_key, :client_uuid,
        ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, :accuracy_m,
        :client_captured_at, :pile_size, :comment, :citizen_type, :zone_id, :status,
        :received_at, :training_consent, :is_demo, :flag_imprecise_position
    )
    """
)

_INSERT_PHOTO = text(
    """
    INSERT INTO report_photos (id, report_id, object_key, sha256, width, height, created_at)
    VALUES (:id, :report_id, :object_key, :sha256, :width, :height, :created_at)
    """
)


@dataclass(frozen=True)
class NewReport:
    id: UUID
    tracking_number: str
    owner_key: str
    client_uuid: UUID
    lat: float
    lng: float
    accuracy_m: float
    client_captured_at: datetime
    pile_size: str
    comment: str | None
    citizen_type: str | None
    zone_id: str
    status: str
    received_at: datetime
    training_consent: bool
    is_demo: bool
    flag_imprecise_position: bool


@dataclass(frozen=True)
class NewReportPhoto:
    id: UUID
    report_id: UUID
    object_key: str
    sha256: str
    width: int
    height: int
    created_at: datetime


def next_tracking_n(year: int) -> int:
    """Rang suivant de l'année, atomique même en création simultanée (AD-18)."""
    return int(current_session().execute(_NEXT_TRACKING_N, {"year": year}).scalar_one())


def insert_report(report: NewReport) -> None:
    current_session().execute(_INSERT_REPORT, report.__dict__)


def insert_photo(photo: NewReportPhoto) -> None:
    current_session().execute(_INSERT_PHOTO, photo.__dict__)
