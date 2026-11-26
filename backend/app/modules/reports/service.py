"""Service du module `reports` : création d'un Signalement anonyme (story 1.11).

Tout est contrôlé avant la première écriture : consentement, puis Zone active, puis la
photo par `core.storage.ingest_photo()` (l'objet S3 est l'effet le plus coûteux à
défaire). Une exception après le stockage annule l'unité de travail : aucune ligne
n'est écrite et l'objet est supprimé par `after_rollback` (story 1.10).
"""

import uuid
from dataclasses import dataclass
from datetime import datetime

from app.core import demo, geo, storage
from app.core.clock import now
from app.core.config import Settings
from app.core.db import current_session, transactional
from app.core.enums import PhotoKind, ReportStatus
from app.core.errors import DomainError, ErrorCode
from app.core.security import Principal
from app.modules.auth import service as auth_service
from app.modules.reports import repository
from app.modules.reports.schemas import ReportMeta


@dataclass(frozen=True)
class CreatedReport:
    id: uuid.UUID
    tracking_number: str
    status: ReportStatus
    received_at: datetime
    is_demo: bool


def tracking_number(year: int, n: int) -> str:
    """Numéro de suivi `TC-AAAA-NNNNNN`."""
    return f"TC-{year:04d}-{n:06d}"


def is_imprecise(accuracy_m: float, threshold_m: int) -> bool:
    """Drapeau « position imprécise » : strictement au-delà du seuil (le seuil exact passe)."""
    return accuracy_m > threshold_m


@transactional
def create(
    principal: Principal,
    meta: ReportMeta,
    photo: bytes,
    settings: Settings,
    voice: bytes | None = None,
) -> CreatedReport:
    """Enregistre un Signalement `pending_review` et renvoie son Numéro de suivi."""
    if not meta.consent.terms:
        raise DomainError(ErrorCode.CONSENT_REQUIRED, 422)

    session = current_session()
    if not geo.in_zone(session, settings.active_zone_id, meta.lat, meta.lng):
        raise DomainError(ErrorCode.OUTSIDE_ACTIVE_ZONE, 422)
    zone = geo.zone_of(session, meta.lat, meta.lng)
    if zone is None:  # dans la Zone active, donc au moins dans Dakar : incohérence des Zones
        raise RuntimeError("Position dans la Zone active mais hors de toute Zone.")

    report_id = uuid.uuid4()
    photo_id = uuid.uuid4()
    stored = storage.ingest_photo(PhotoKind.REPORT, photo, photo_id=photo_id)
    # Note vocale facultative, rangée seulement si tout le reste est accepté.
    voice_key = storage.ingest_voice(voice, report_id).object_key if voice else None

    received_at = now()
    number = tracking_number(received_at.year, repository.next_tracking_n(received_at.year))
    is_demo = demo.flag(settings=settings)

    auth_service.touch_device(principal.device_hash, meta.consent.training, received_at)
    repository.insert_report(
        repository.NewReport(
            id=report_id,
            tracking_number=number,
            owner_key=principal.owner_key,
            client_uuid=meta.client_uuid,
            lat=meta.lat,
            lng=meta.lng,
            accuracy_m=meta.accuracy_m,
            client_captured_at=meta.captured_at,
            pile_size=meta.pile_size.value,
            comment=meta.comment,
            citizen_type=meta.waste_type.value if meta.waste_type else None,
            zone_id=zone.id,
            status=ReportStatus.PENDING_REVIEW.value,
            received_at=received_at,
            training_consent=meta.consent.training,
            is_demo=is_demo,
            flag_imprecise_position=is_imprecise(meta.accuracy_m, settings.report_accuracy_flag_m),
            voice_key=voice_key,
        )
    )
    repository.insert_photo(
        repository.NewReportPhoto(
            id=photo_id,
            report_id=report_id,
            object_key=stored.object_key,
            sha256=stored.sha256,
            width=stored.width,
            height=stored.height,
            created_at=received_at,
        )
    )
    return CreatedReport(
        id=report_id,
        tracking_number=number,
        status=ReportStatus.PENDING_REVIEW,
        received_at=received_at,
        is_demo=is_demo,
    )
