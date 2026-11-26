"""Routes du module `reports` : `POST /v1/reports` (story 1.11), route publique d'AD-9.

`multipart/form-data` : `meta` (JSON, `ReportMeta`) et `photo` (octets de l'image).
Ordre des contrôles : principal (dépendance, avant le corps), forme de `meta` et
présence de `photo`, puis le service (consentement, Zone active, photo, écritures).
"""

from typing import Annotated

from fastapi import APIRouter, File, Form, Request, UploadFile
from pydantic import ValidationError

from app.core.db import UowSession
from app.core.errors import ErrorResponse, field_name, validation_error
from app.core.security import CurrentPrincipal
from app.core.storage import MAX_PHOTO_BYTES, MAX_VOICE_BYTES
from app.modules.reports import service
from app.modules.reports.schemas import ReportCreated, ReportMeta

router = APIRouter(prefix="/v1", tags=["signalements"])


def parse_meta(raw: str) -> ReportMeta:
    """`meta` validé ; 422 `validation_error` nommant les champs (`meta.lat`), sans valeur."""
    try:
        return ReportMeta.model_validate_json(raw)
    except ValidationError as exc:
        fields = [
            # Le nom d'un champ inconnu est un texte du client : jamais recopié.
            "meta (champ inconnu)"
            if error["type"] == "extra_forbidden"
            else field_name(error["loc"], prefix="meta")
            for error in exc.errors(include_url=False, include_input=False)
        ]
        raise validation_error(fields) from None


@router.post(
    "/reports",
    status_code=201,
    responses={
        400: {"model": ErrorResponse, "description": "Identifiant d'appareil invalide"},
        401: {"model": ErrorResponse, "description": "Jeton invérifiable"},
        413: {"model": ErrorResponse, "description": "Photo trop lourde"},
        415: {"model": ErrorResponse, "description": "Type de photo non accepté"},
        422: {"model": ErrorResponse, "description": "Champ invalide, consentement, Zone"},
    },
)
def create_report(
    request: Request,
    principal: CurrentPrincipal,
    session: UowSession,
    meta: Annotated[str, Form(description="ReportMeta en JSON")],
    photo: Annotated[UploadFile, File(description="Photo JPEG, PNG ou WebP, 1 Mo au plus")],
    voice: Annotated[
        UploadFile | None,
        File(description="Note vocale facultative (WebM, Ogg ou MP4), 600 Ko au plus"),
    ] = None,
) -> ReportCreated:
    """Crée un Signalement anonyme et renvoie son Numéro de suivi."""
    report_meta = parse_meta(meta)
    # Un octet de plus que le plafond : assez pour que `ingest_photo` refuse en 413.
    # python-multipart a déjà reçu la partie (sur disque au-delà de son seuil) : la
    # limite de taille du corps relève du bord HTTP (Caddy, story 8.4).
    data = photo.file.read(MAX_PHOTO_BYTES + 1)
    voice_data = voice.file.read(MAX_VOICE_BYTES + 1) if voice is not None else None
    created = service.create(
        principal, report_meta, data, request.app.state.settings, voice=voice_data or None
    )
    return ReportCreated(
        id=created.id,
        tracking_number=created.tracking_number,
        status=created.status,
        received_at=created.received_at,
        is_demo=created.is_demo,
    )
