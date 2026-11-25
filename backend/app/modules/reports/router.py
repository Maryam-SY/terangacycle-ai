"""Routes du module reports.

`POST /v1/reports` : route publique du Citoyen anonyme (liste blanche d'AD-9), identifié
par `X-Device-Id`, exemptée d'`Idempotency-Key` (AD-5). Corps `multipart/form-data` :
`meta` (JSON, `ReportMeta`) et `photo`.

Avant toute lecture du corps, la garde `ReportUploadGuard` (middleware ASGI) refuse :
`X-Device-Id` absent ou invalide → 400 `invalid_device_id`, puis `Authorization` présent
→ 401 `invalid_token` (400 l'emporte sur 401), puis `Content-Length` au-delà de 2 Mio →
413 `photo_too_large`. Un corps mal formé ou énorme n'est donc jamais lu ni écrit sur
disque pour une requête anonyme ; Caddy borne aussi le corps à 2 Mo (`infra/Caddyfile`).

Route synchrone (`def`, pool de threads) : le service ouvre l'unité de travail synchrone
(`@transactional`). Le principal est recontrôlé (dépendance), puis `meta` ; la photo est
lue sur au plus 1 Mo + 1 octet avant d'être confiée à `ingest_photo()`. Les réglages sont
ceux avec lesquels l'application a été construite (`request.app.state.settings`).
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from starlette.datastructures import Headers
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core import security
from app.core.errors import DomainError, ErrorCode, ErrorResponse, error_response
from app.core.security import Principal
from app.core.storage import MAX_PHOTO_BYTES
from app.modules.reports import service
from app.modules.reports.schemas import ReportCreated, parse_meta

router = APIRouter(prefix="/v1", tags=["reports"])

REPORTS_PATH = "/v1/reports"
# Corps entier (photo d'au plus 1 Mo, `meta` et enveloppe multipart) : 2 Mio au plus.
MAX_REPORT_BODY_BYTES = 2 * 1024 * 1024
# Un octet de plus que le plafond : assez pour que `ingest_photo()` refuse (413) une photo
# trop lourde, sans jamais charger en mémoire un fichier énorme.
PHOTO_READ_LIMIT = MAX_PHOTO_BYTES + 1


def _error(description: str) -> dict[str, Any]:
    return {"model": ErrorResponse, "description": description}


# Contrat d'erreur de la route, publié dans l'OpenAPI (client généré, story 1.13).
ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: _error("`invalid_device_id` : X-Device-Id absent ou invalide."),
    401: _error("`invalid_token` : en-tête Authorization présent (non vérifiable)."),
    413: _error("`photo_too_large` : photo de plus de 1 Mo, ou corps de plus de 2 Mio."),
    415: _error("`unsupported_media_type` : photo ni JPEG, ni PNG, ni WebP."),
    422: _error(
        "`validation_error` (champ nommé), `consent_required`, `outside_active_zone`, "
        "`photo_too_many_pixels`, `photo_unreadable`."
    ),
    503: _error("`storage_unavailable` : stockage des photos indisponible."),
}


class ReportUploadGuard:
    """Middleware ASGI : contrôles de `POST /v1/reports` faits sur les seuls en-têtes,
    avant que le corps ne soit lu. Réponse dans l'enveloppe d'erreur habituelle."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["method"] == "POST" and scope["path"] == REPORTS_PATH:
            error = _header_error(Headers(scope=scope))
            if error is not None:
                request_id = scope.get("state", {}).get("request_id", "")
                response = error_response(error.http_status, error.code, request_id, error.message)
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)


def _header_error(headers: Headers) -> DomainError | None:
    try:
        security.check_identity_headers(headers)
    except DomainError as exc:
        return exc
    length = headers.get("content-length", "")
    if length.isdigit() and int(length) > MAX_REPORT_BODY_BYTES:
        return DomainError(ErrorCode.PHOTO_TOO_LARGE, 413)
    return None


@router.post(
    "/reports",
    status_code=201,
    summary="Envoyer un Signalement",
    responses=ERROR_RESPONSES,
)
def create_report(
    request: Request,
    principal: Annotated[Principal, Depends(security.principal)],
    meta: Annotated[
        str,
        Form(
            description=(
                "Métadonnées en JSON : client_uuid, lat, lng, accuracy_m, heap_size, "
                "comment, waste_type, captured_at, consent {terms, training}."
            )
        ),
    ],
    photo: Annotated[
        UploadFile, File(description="Photo du dépôt : JPEG, PNG ou WebP, 1 Mo au plus.")
    ],
) -> ReportCreated:
    parsed = parse_meta(meta)
    data = photo.file.read(PHOTO_READ_LIMIT)
    return service.create_report(principal, parsed, data, request.app.state.settings)
