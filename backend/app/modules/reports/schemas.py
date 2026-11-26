"""Schémas de `POST /v1/reports` (story 1.11).

`meta` arrive en JSON dans un champ du formulaire multipart : `parse_meta()` le valide
(champs inconnus refusés, types stricts) et transforme toute erreur en 422
`validation_error` qui nomme le champ, jamais sa valeur.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any
from uuid import UUID

from pydantic import (
    UUID4,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
)

from app.core import clock
from app.core.enums import HeapSize, ReportStatus, WasteType
from app.core.errors import field_of, validation_error

# Commentaire du Citoyen : 280 caractères au plus après retrait des blancs de bord, comptés
# en points de code Unicode ; vide ou blanc → aucun commentaire (NULL).
COMMENT_MAX_CHARS = 280
# Heure de l'appareil : bornée pour rester lisible et comparable (ni an 1, ni an 9999).
CAPTURED_AT_MIN = datetime(2000, 1, 1, tzinfo=UTC)
CAPTURED_AT_MAX_AHEAD = timedelta(days=1)
META_FIELD = "meta"


class ReportConsent(BaseModel):
    """Consentements donnés sur l'appareil (AD-24)."""

    model_config = ConfigDict(extra="forbid", strict=True)

    # Conditions d'utilisation : absentes ou refusées → 422 `consent_required`, contrôlé
    # après la validation du schéma.
    terms: bool | None = None
    # Usage pour le Modèle (case séparée, jamais exigée) : copié sur le Signalement.
    training: bool


class ReportMeta(BaseModel):
    """Métadonnées d'un Signalement. `captured_at` (heure de l'appareil) est gardée à part
    et ne sert jamais à décider : le serveur date la réception par `core.clock`."""

    model_config = ConfigDict(extra="forbid", strict=True)

    # Identifiant client : UUID version 4, tiré par un générateur cryptographique sur
    # l'appareil (`crypto.randomUUID()`), une fois par Signalement (story 1.12).
    client_uuid: UUID4
    lat: Annotated[float, Field(ge=-90, le=90, allow_inf_nan=False)]
    lng: Annotated[float, Field(ge=-180, le=180, allow_inf_nan=False)]
    accuracy_m: Annotated[float, Field(gt=0, allow_inf_nan=False)]
    heap_size: HeapSize
    comment: Annotated[str, Field(max_length=COMMENT_MAX_CHARS)] | None = None
    waste_type: WasteType | None = None
    captured_at: AwareDatetime
    consent: ReportConsent | None = None

    @field_validator("comment", mode="before")
    @classmethod
    def _strip_comment(cls, value: Any) -> Any:
        # Avant la limite de 280 : elle s'applique au texte sans ses blancs de bord.
        if isinstance(value, str):
            return value.strip() or None
        return value

    @field_validator("captured_at")
    @classmethod
    def _plausible_capture_time(cls, value: datetime) -> datetime:
        # Bornes larges : l'heure de l'appareil n'est jamais utilisée pour décider.
        if not CAPTURED_AT_MIN <= value <= clock.now() + CAPTURED_AT_MAX_AHEAD:
            raise ValueError("heure de prise de vue hors bornes")
        return value

    @field_validator("comment")
    @classmethod
    def _no_nul_character(cls, value: str | None) -> str | None:
        # PostgreSQL refuse le caractère nul dans un texte : refus net plutôt qu'une 500.
        if value is not None and "\x00" in value:
            raise ValueError("caractère nul interdit")
        return value


class ReportCreated(BaseModel):
    """Réponse 201, et 200 d'un renvoi (story 1.12) : exactement ces champs. Ni
    `owner_key`, ni empreinte, ni Identifiant d'appareil, ni Organisation responsable."""

    id: UUID
    tracking_number: str
    status: ReportStatus
    # UTC, sérialisé en ISO 8601 avec `Z`.
    received_at: datetime
    is_demo: bool


@dataclass(frozen=True, slots=True)
class ReportOutcome:
    """Résultat de `POST /v1/reports` : le Signalement (mêmes champs en 201 et en 200) et
    `replayed`, vrai pour un renvoi idempotent (200, rien n'a été écrit)."""

    report: ReportCreated
    replayed: bool


def parse_meta(raw: str) -> ReportMeta:
    """`meta` validé, ou 422 `validation_error` nommant les champs fautifs (`meta.lat`)."""
    try:
        return ReportMeta.model_validate_json(raw)
    except ValidationError as exc:
        errors = exc.errors(include_url=False, include_input=False, include_context=False)
        fields = [field_of(error["loc"], prefix=META_FIELD) for error in errors]
        raise validation_error(fields) from None
