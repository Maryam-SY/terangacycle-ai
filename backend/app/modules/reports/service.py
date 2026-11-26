"""Service du module reports : création d'un Signalement (story 1.11), renvoi
idempotent (story 1.12) et miniature de sa photo (story 1.18).

Miniature : la création met en file la tâche arq `thumb:<photo_id>` par `core.jobs`, après
le commit seulement (jamais après une annulation, jamais pour un renvoi idempotent, qui
n'écrit rien). Le worker appelle `make_thumbnail(photo_id)`.

`create_report()` cherche d'abord le Signalement par son Identifiant client (story 1.12) :
- même auteur (`owner_key`) : l'existant est renvoyé tel qu'enregistré (200), sans lire
  ni stocker la photo, sans toucher au compteur ni rien écrire ; le contenu renvoyé n'est
  jamais comparé ni appliqué ;
- autre auteur : 409 `client_uuid_conflict`, sans rien du Signalement d'origine.

Sinon, il contrôle, dans l'ordre, pour qu'un refus n'écrive jamais rien : consentement aux
conditions (422 `consent_required`), Position dans la Zone active (422
`outside_active_zone`), photo (`core.storage.ingest_photo`, 413, 415 ou 422) ; puis il
écrit, dans l'unité de travail en cours : appareil (`auth.service.touch_device`, Principal
`device` seulement), Numéro de suivi, Signalement et photo. Une exception après le
stockage annule tout et supprime l'objet (`after_rollback`, story 1.10).

Envois simultanés du même Identifiant client, du même auteur ou de deux auteurs : l'unité
de la création prend d'abord un verrou de transaction sur le `client_uuid`
(`pg_advisory_xact_lock`), avant la recherche. Le second envoi attend le commit du premier,
puis la recherche le résout : 200 (même auteur, sans lire ni stocker la photo) ou 409
(autre auteur).

Filet de sécurité : une insertion qui viole quand même l'unicité `(client_uuid, owner_key)`
(migration 0004) annule toute son unité (ni ligne, ni Numéro consommé, photo supprimée),
puis l'existant est relu dans une nouvelle unité : 200, ou 409 si aucun Signalement de
l'auteur n'y est. Seule la violation de cette contrainte est traitée ainsi, et seulement
quand `create_report()` a ouvert sa propre unité : un appelant qui l'a rejointe reçoit
l'erreur, son unité étant perdue.

Calculés par le serveur (AD-6) : `received_at`, lu une fois (`core.clock`, UTC), qui donne
l'année du Numéro et l'année et le mois de la clé de la photo ; Zones qui couvrent la
Position, lues une fois (`core.geo.zones_covering`) : la plus précise devient `zone_id`, et
la liste choisit l'Organisation responsable (`orgs.service.responsible_org`) ; drapeau de
Position imprécise et `is_demo` (`core.demo.flag`), d'après les réglages de l'application ;
Statut `pending_review`.

Journaux : l'`id` et le Numéro de suivi seulement (plus `replayed=true` pour un renvoi),
jamais une Position, un Identifiant d'appareil, une empreinte ni `owner_key` ; un conflit
ne journalise aucun identifiant du Signalement d'origine.
"""

import functools
from collections.abc import Callable
from datetime import UTC
from pathlib import PurePosixPath
from uuid import UUID, uuid4

from app.core import clock, demo, geo, jobs, storage
from app.core.config import Settings
from app.core.db import after_commit, current_session, in_unit_of_work, transactional
from app.core.enums import PhotoKind, ReportStatus
from app.core.errors import DomainError, ErrorCode
from app.core.logging import get_logger
from app.core.security import Principal
from app.modules.auth import service as auth_service
from app.modules.orgs import service as orgs_service
from app.modules.reports import repository
from app.modules.reports.rules import format_tracking_number, is_imprecise
from app.modules.reports.schemas import ReportCreated, ReportMeta, ReportOutcome

log = get_logger(__name__)

# Lecture des octets de la photo, appelée seulement quand un Signalement est créé.
PhotoReader = Callable[[], bytes]
CreateReport = Callable[[Principal, ReportMeta, PhotoReader, Settings], ReportOutcome]

# Tâche arq de la miniature d'une photo (story 1.18), d'identifiant `thumb:<photo_id>`.
THUMB_JOB = "thumb"


def _thumb_job_id(photo_id: UUID) -> str:
    """Identifiant de la tâche de miniature : `thumb:<photo_id>` (`report_photos.id`)."""
    return f"{THUMB_JOB}:{photo_id}"


def _photo_id(object_key: str) -> UUID:
    # AD-13 : l'`<uuid>` de la clé `report/<aaaa>/<mm>/<uuid>.jpg` est celui de la ligne.
    return UUID(PurePosixPath(object_key).stem)


def _log_created(report_id: UUID, tracking_number: str) -> None:
    log.info("report_created", report_id=str(report_id), tracking_number=tracking_number)


def _log_replayed(report_id: UUID, tracking_number: str) -> None:
    log.info(
        "report_replayed", report_id=str(report_id), tracking_number=tracking_number, replayed=True
    )


def _existing_outcome(principal: Principal, client_uuid: UUID) -> ReportOutcome | None:
    """Renvoi de l'auteur (200), 409 `client_uuid_conflict` si l'Identifiant client est à
    un autre auteur, ou `None` s'il est libre. N'écrit rien."""
    own = repository.find_own_report(principal.owner_key, client_uuid)
    if own is None:
        if repository.client_uuid_taken(client_uuid):
            log.info("report_client_uuid_conflict")
            raise DomainError(ErrorCode.CLIENT_UUID_CONFLICT, 409)
        return None
    after_commit(_log_replayed, own.id, own.tracking_number)
    return ReportOutcome(
        report=ReportCreated(
            id=own.id,
            tracking_number=own.tracking_number,
            status=ReportStatus(own.status),
            received_at=own.received_at.astimezone(UTC),
            is_demo=own.is_demo,
        ),
        replayed=True,
    )


@transactional
def _reread_after_race(principal: Principal, client_uuid: UUID) -> ReportOutcome | None:
    """Relecture, dans une nouvelle unité de travail, après une insertion perdue."""
    return _existing_outcome(principal, client_uuid)


def _settle_parallel_sends(create: CreateReport) -> CreateReport:
    """Autour de l'unité de la création : un envoi parallèle perdu (violation de
    `uq_reports_client_uuid_owner_key`, unité annulée) est résolu par une relecture."""

    @functools.wraps(create)
    def settle(
        principal: Principal, meta: ReportMeta, read_photo: PhotoReader, settings: Settings
    ) -> ReportOutcome:
        joined = in_unit_of_work()
        try:
            return create(principal, meta, read_photo, settings)
        except repository.ClientUuidTakenError:
            if joined:
                # L'unité de l'appelant est perdue : impossible d'y relire.
                raise
            outcome = _reread_after_race(principal, meta.client_uuid)
            if outcome is None:
                # Aucun Signalement de l'auteur à relire : l'Identifiant client reste pris.
                raise DomainError(ErrorCode.CLIENT_UUID_CONFLICT, 409) from None
            return outcome

    return settle


@_settle_parallel_sends
@transactional
def create_report(
    principal: Principal, meta: ReportMeta, read_photo: PhotoReader, settings: Settings
) -> ReportOutcome:
    """Enregistre un Signalement et lui attribue son Numéro de suivi (`replayed` faux,
    201), ou renvoie celui que le même auteur a déjà envoyé avec le même Identifiant
    client (`replayed` vrai, 200).

    `read_photo` : lecture des octets de la photo, appelée seulement pour une création.
    `settings` : les réglages avec lesquels l'application a été construite.
    """
    # Verrou d'abord : un envoi simultané du même `client_uuid` attend notre commit, puis
    # nous trouve à la recherche.
    repository.lock_client_uuid(meta.client_uuid)
    existing = _existing_outcome(principal, meta.client_uuid)
    if existing is not None:
        return existing

    received_at = clock.now().astimezone(UTC)
    consent = meta.consent
    if consent is None or consent.terms is not True:
        raise DomainError(ErrorCode.CONSENT_REQUIRED, 422)

    session = current_session()
    if not geo.in_zone(session, settings.active_zone_id, meta.lat, meta.lng):
        raise DomainError(ErrorCode.OUTSIDE_ACTIVE_ZONE, 422)
    # Dans la Zone active, une Zone au moins couvre le point (la Zone active elle-même).
    zones = geo.zones_covering(session, meta.lat, meta.lng)
    if not zones:
        raise DomainError(ErrorCode.OUTSIDE_ACTIVE_ZONE, 422)

    stored = storage.ingest_photo(PhotoKind.REPORT, read_photo(), at=received_at)

    organization_id = orgs_service.responsible_org(zones)
    if principal.device_hash is not None:
        auth_service.touch_device(
            principal.device_hash, training_consent=consent.training, seen_at=received_at
        )
    # Compteur en dernier : sa ligne reste verrouillée jusqu'au commit.
    sequence = repository.next_tracking_sequence(received_at.year)
    tracking_number = format_tracking_number(received_at.year, sequence)
    report_id = uuid4()
    is_demo = demo.flag(settings)
    # Envoi parallèle du même Signalement déjà enregistré : `ClientUuidTakenError`, l'unité
    # est annulée (compteur compris) et l'objet supprimé (`_settle_parallel_sends`).
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
            zone_id=zones[0].id,
            received_at=received_at,
            client_captured_at=meta.captured_at,
            flag_imprecise_position=is_imprecise(meta.accuracy_m, settings.report_accuracy_flag_m),
            training_consent=consent.training,
            is_demo=is_demo,
        )
    )
    photo_id = _photo_id(stored.object_key)
    repository.insert_photo(
        repository.NewPhoto(
            id=photo_id,
            report_id=report_id,
            object_key=stored.object_key,
            sha256=stored.sha256,
            width=stored.width,
            height=stored.height,
            created_at=received_at,
        )
    )
    after_commit(_log_created, report_id, tracking_number)
    # Miniature (story 1.18) : mise en file après le commit seulement, jamais après une
    # annulation ; un échec de la mise en file ne change ni le commit ni la réponse.
    jobs.enqueue_after_commit(THUMB_JOB, str(photo_id), job_id=_thumb_job_id(photo_id))
    return ReportOutcome(
        report=ReportCreated(
            id=report_id,
            tracking_number=tracking_number,
            status=ReportStatus.PENDING_REVIEW,
            received_at=received_at,
            is_demo=is_demo,
        ),
        replayed=False,
    )


@transactional
def make_thumbnail(photo_id: UUID) -> str | None:
    """Produit la miniature de la photo `photo_id` et enregistre sa clé (tâche `thumb`,
    story 1.18) ; renvoie la clé, ou `None` si rien n'a pu être fait.

    Sous le verrou de la ligne (`FOR UPDATE`), l'état est relu : photo absente (Signalement
    retiré) ou miniature déjà enregistrée, la tâche s'arrête sans rien écrire. Sinon la
    miniature est stockée (clé déterministe, `core.storage.make_thumbnail`), puis sa clé
    est écrite si aucune ne l'est encore. Rejouer la tâche, même en parallèle, ne crée donc
    jamais de second objet.

    Photo source absente ou illisible : journal `thumb_source_missing` et arrêt (un nouvel
    essai n'y changerait rien). Stockage indisponible : `DomainError` 503
    `storage_unavailable`, l'unité est annulée et le worker réessaie.
    """
    photo = repository.lock_photo(photo_id)
    if photo is None:
        log.info("thumb_photo_gone", photo_id=str(photo_id))
        return None
    if photo.thumb_key is not None:
        log.info("thumb_already_recorded", photo_id=str(photo_id), thumb_key=photo.thumb_key)
        return photo.thumb_key
    try:
        thumb_key = storage.make_thumbnail(photo.object_key)
    except storage.ThumbnailSourceError:
        log.warning("thumb_source_missing", photo_id=str(photo_id), object_key=photo.object_key)
        return None
    repository.set_thumb_key(photo_id, thumb_key)
    after_commit(_log_thumb_recorded, photo_id, thumb_key)
    return thumb_key


def _log_thumb_recorded(photo_id: UUID, thumb_key: str) -> None:
    log.info("thumb_recorded", photo_id=str(photo_id), thumb_key=thumb_key)
