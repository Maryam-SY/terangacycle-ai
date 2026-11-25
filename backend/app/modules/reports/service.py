"""Service du module reports : création d'un Signalement (story 1.11).

`create_report()` contrôle, dans l'ordre, pour qu'un refus n'écrive jamais rien :
consentement aux conditions (422 `consent_required`), Position dans la Zone active
(422 `outside_active_zone`), photo (`core.storage.ingest_photo`, 413, 415 ou 422) ; puis
il écrit, dans l'unité de travail en cours : appareil (`auth.service.touch_device`),
Numéro de suivi, Signalement et photo. Une exception après le stockage annule tout et
supprime l'objet (`after_rollback`, story 1.10).

Calculés par le serveur (AD-6) : `received_at` et l'année du Numéro (`core.clock`, UTC),
Zone (`core.geo.zone_of`), Organisation responsable (`orgs.service.responsible_org`),
drapeau de Position imprécise, `is_demo` (`core.demo.flag`), Statut `pending_review`.

Journaux : l'`id` et le Numéro de suivi seulement, jamais une Position, un Identifiant
d'appareil, une empreinte ni `owner_key`.
"""

from datetime import UTC
from pathlib import PurePosixPath
from uuid import UUID, uuid4

from app.core import clock, demo, geo, storage
from app.core.config import get_settings
from app.core.db import after_commit, current_session, transactional
from app.core.enums import PhotoKind, ReportStatus
from app.core.errors import DomainError, ErrorCode
from app.core.logging import get_logger
from app.core.security import Principal
from app.modules.auth import service as auth_service
from app.modules.orgs import service as orgs_service
from app.modules.reports import repository
from app.modules.reports.rules import format_tracking_number, is_imprecise
from app.modules.reports.schemas import ReportCreated, ReportMeta

log = get_logger(__name__)


def _photo_id(object_key: str) -> UUID:
    # AD-13 : l'`<uuid>` de la clé `report/<aaaa>/<mm>/<uuid>.jpg` est celui de la ligne.
    return UUID(PurePosixPath(object_key).stem)


def _log_created(report_id: UUID, tracking_number: str) -> None:
    log.info("report_created", report_id=str(report_id), tracking_number=tracking_number)


@transactional
def create_report(principal: Principal, meta: ReportMeta, photo: bytes) -> ReportCreated:
    """Enregistre un Signalement anonyme et lui attribue son Numéro de suivi."""
    consent = meta.consent
    if consent is None or consent.terms is not True:
        raise DomainError(ErrorCode.CONSENT_REQUIRED, 422)

    session = current_session()
    if not geo.in_active_zone(session, meta.lat, meta.lng):
        raise DomainError(ErrorCode.OUTSIDE_ACTIVE_ZONE, 422)
    # Dans la Zone active, une Zone au moins couvre le point (la Zone active elle-même).
    zone = geo.zone_of(session, meta.lat, meta.lng)
    if zone is None:
        raise DomainError(ErrorCode.OUTSIDE_ACTIVE_ZONE, 422)

    stored = storage.ingest_photo(PhotoKind.REPORT, photo)

    received_at = clock.now().astimezone(UTC)
    organization_id = orgs_service.responsible_org(meta.lat, meta.lng)
    auth_service.touch_device(
        principal.device_hash, training_consent=consent.training, seen_at=received_at
    )
    # Compteur en dernier : sa ligne reste verrouillée jusqu'au commit.
    sequence = repository.next_tracking_sequence(received_at.year)
    tracking_number = format_tracking_number(received_at.year, sequence)
    report_id = uuid4()
    is_demo = demo.flag()
    repository.insert_report(
        repository.NewReport(
            id=report_id,
            tracking_number=tracking_number,
            owner_key=principal.owner_key,
            client_uuid=meta.client_uuid,
            organization_id=organization_id,
            status=ReportStatus.PENDING_REVIEW.value,
            lat=meta.lat,
            lng=meta.lng,
            accuracy_m=meta.accuracy_m,
            heap_size=meta.heap_size.value,
            comment=meta.comment,
            citizen_type=meta.waste_type.value if meta.waste_type else None,
            zone_id=zone.id,
            received_at=received_at,
            client_captured_at=meta.captured_at,
            flag_imprecise_position=is_imprecise(
                meta.accuracy_m, get_settings().report_accuracy_flag_m
            ),
            training_consent=consent.training,
            is_demo=is_demo,
        )
    )
    repository.insert_photo(
        repository.NewPhoto(
            id=_photo_id(stored.object_key),
            report_id=report_id,
            object_key=stored.object_key,
            sha256=stored.sha256,
            width=stored.width,
            height=stored.height,
            created_at=received_at,
        )
    )
    after_commit(_log_created, report_id, tracking_number)
    return ReportCreated(
        id=report_id,
        tracking_number=tracking_number,
        status=ReportStatus.PENDING_REVIEW,
        received_at=received_at,
        is_demo=is_demo,
    )
