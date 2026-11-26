"""Contrat HTTP de la création d'un Signalement (story 1.11).

`meta` arrive en JSON dans un champ du formulaire multipart, à côté de `photo`.
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator

from app.core.enums import PileSize, ReportStatus, WasteType

COMMENT_MAX_CHARS = 280

Latitude = Annotated[float, Field(ge=-90, le=90, allow_inf_nan=False)]
Longitude = Annotated[float, Field(ge=-180, le=180, allow_inf_nan=False)]


class Consent(BaseModel):
    """Consentement lu dans Dexie `meta` par la PWA. `terms` absent vaut refus."""

    model_config = ConfigDict(extra="forbid", strict=True)

    terms: bool = False
    training: bool = False


class ReportMeta(BaseModel):
    """Champs du Signalement envoyés avec la photo ; tout champ inconnu est refusé."""

    model_config = ConfigDict(extra="forbid", strict=True)

    client_uuid: UUID
    lat: Latitude
    lng: Longitude
    accuracy_m: Annotated[float, Field(gt=0, le=100_000, allow_inf_nan=False)]
    captured_at: AwareDatetime
    pile_size: PileSize
    # Points de code Unicode (len() de Python, char_length() de PostgreSQL).
    comment: Annotated[str, Field(max_length=COMMENT_MAX_CHARS)] | None = None
    waste_type: WasteType | None = None
    consent: Consent = Field(default_factory=Consent)

    @field_validator("comment")
    @classmethod
    def _clean_comment(cls, value: str | None) -> str | None:
        """Sans caractère NUL (refusé par PostgreSQL) ; vide ou blanc : pas de commentaire."""
        if value is None:
            return None
        if "\x00" in value:
            raise ValueError("caractère nul interdit")
        return value if value.strip() else None


class ReportCreated(BaseModel):
    """Réponse 201 : ni `owner_key`, ni empreinte, ni Identifiant d'appareil."""

    id: UUID
    tracking_number: str
    status: ReportStatus
    received_at: datetime
    is_demo: bool
