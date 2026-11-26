"""Accès aux tables `reports`, `report_photos` et `tracking_counters` (propriété de
`reports`, AD-2). Aucun contrôle de transaction ici (AD-17)."""

from dataclasses import asdict, dataclass
from datetime import datetime
from uuid import UUID

from psycopg import errors as pg_errors
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.db import current_session

# Unicité de l'Identifiant client par auteur (migration 0004, story 1.12), colonnes
# `(client_uuid, owner_key)` : son index sert aussi la recherche par seul `client_uuid`.
CLIENT_UUID_CONSTRAINT = "uq_reports_client_uuid_owner_key"

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

# Verrou de transaction sur l'Identifiant client, levé au commit ou à l'annulation : deux
# envois du même `client_uuid`, de n'importe quels auteurs, se suivent au lieu de se croiser.
_LOCK_CLIENT_UUID = text(
    "SELECT pg_advisory_xact_lock(hashtextextended(CAST(:client_uuid AS text), 0))"
)

# Signalement de cet auteur pour cet Identifiant client (index unique complet).
_OWN_REPORT = text(
    """
    SELECT id, tracking_number, status, received_at, is_demo FROM reports
    WHERE client_uuid = :client_uuid AND owner_key = :owner_key
    """
)

# Identifiant client déjà pris, quel que soit l'auteur (préfixe de l'index unique). Rien
# d'autre n'est lu du Signalement d'un autre auteur.
_CLIENT_UUID_TAKEN = text("SELECT EXISTS (SELECT 1 FROM reports WHERE client_uuid = :client_uuid)")

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
class StoredReport:
    """Champs d'un Signalement enregistré que son auteur peut relire (réponse d'un renvoi)."""

    id: UUID
    tracking_number: str
    status: str
    received_at: datetime
    is_demo: bool


class ClientUuidTakenError(Exception):
    """L'insertion viole `uq_reports_client_uuid_owner_key` : le même auteur a déjà
    enregistré ce Signalement (envoi parallèle). L'unité de travail est perdue."""


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


def lock_client_uuid(client_uuid: UUID) -> None:
    """Attend, puis tient jusqu'à la fin de l'unité de travail, le verrou de l'Identifiant
    client : un envoi concurrent du même `client_uuid` attend le commit du premier."""
    current_session().execute(_LOCK_CLIENT_UUID, {"client_uuid": client_uuid})


def find_own_report(owner_key: str, client_uuid: UUID) -> StoredReport | None:
    """Signalement de l'auteur `owner_key` pour cet Identifiant client, s'il existe."""
    row = (
        current_session()
        .execute(_OWN_REPORT, {"owner_key": owner_key, "client_uuid": client_uuid})
        .one_or_none()
    )
    return None if row is None else StoredReport(**row._asdict())


def client_uuid_taken(client_uuid: UUID) -> bool:
    """Vrai si un Signalement, de n'importe quel auteur, porte cet Identifiant client."""
    taken = current_session().execute(_CLIENT_UUID_TAKEN, {"client_uuid": client_uuid})
    return bool(taken.scalar_one())


def is_client_uuid_violation(exc: IntegrityError) -> bool:
    """Vrai seulement pour une violation de la contrainte `CLIENT_UUID_CONSTRAINT`."""
    cause = exc.orig
    return (
        isinstance(cause, pg_errors.UniqueViolation)
        and cause.diag.constraint_name == CLIENT_UUID_CONSTRAINT
    )


def insert_report(report: NewReport) -> None:
    """Insère le Signalement. Une violation de l'unicité `(client_uuid, owner_key)` lève
    `ClientUuidTakenError` ; toute autre erreur reste telle quelle."""
    try:
        current_session().execute(_INSERT_REPORT, asdict(report))
    except IntegrityError as exc:
        if is_client_uuid_violation(exc):
            raise ClientUuidTakenError from exc
        raise


def insert_photo(photo: NewPhoto) -> None:
    current_session().execute(_INSERT_PHOTO, asdict(photo))
