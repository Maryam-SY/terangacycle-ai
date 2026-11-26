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
(`@transactional`). Le principal est recontrôlé (dépendance), puis `meta` ; la photo n'est
lue (au plus 1 Mo + 1 octet, avant d'être confiée à `ingest_photo()`) que si le service
crée vraiment un Signalement. Les réglages sont ceux avec lesquels l'application a été
construite (`request.app.state.settings`).

Renvoi idempotent (story 1.12) : le même auteur qui renvoie le même `meta.client_uuid`
reçoit 200 avec le Signalement déjà enregistré (mêmes champs qu'en 201), sans que rien ne
soit écrit ; un autre auteur reçoit 409 `client_uuid_conflict`, l'enveloppe d'erreur seule.

OpenAPI (story 1.13) : `meta` arrive en texte (`Form`) et reste validé par `parse_meta()`.
Pour le client généré de la PWA, `document_report_body()` décrit ce champ par le schéma
`ReportMeta` (JSON, `encoding.meta.contentType`) et la photo en binaire ; seule la
description change, jamais le traitement de la requête.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, Request, Response, UploadFile
from starlette.datastructures import Headers
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core import security
from app.core.errors import DomainError, ErrorCode, ErrorResponse, error_response
from app.core.security import Principal
from app.core.storage import MAX_PHOTO_BYTES
from app.modules.reports import service
from app.modules.reports.schemas import ReportCreated, ReportMeta, parse_meta

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
    409: _error(
        "`client_uuid_conflict` : Identifiant client déjà utilisé par un autre auteur "
        "(rien du Signalement existant n'est renvoyé)."
    ),
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


# Contrat complet : 201 (création, par défaut), 200 (renvoi idempotent) et les erreurs.
RESPONSES: dict[int | str, dict[str, Any]] = {
    200: {
        "model": ReportCreated,
        "description": (
            "Renvoi idempotent : même auteur, même `meta.client_uuid`. Le Signalement déjà "
            "enregistré (Statut actuel), sans rien écrire ; le contenu renvoyé est ignoré."
        ),
    },
    **ERROR_RESPONSES,
}


@router.post(
    "/reports",
    status_code=201,
    summary="Envoyer un Signalement",
    response_description="Signalement créé, avec son Numéro de suivi.",
    responses=RESPONSES,
)
def create_report(
    request: Request,
    response: Response,
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

    def read_photo() -> bytes:
        return photo.file.read(PHOTO_READ_LIMIT)

    outcome = service.create_report(principal, parsed, read_photo, request.app.state.settings)
    if outcome.replayed:
        response.status_code = 200
    return outcome.report


SCHEMA_REF = "#/components/schemas/{model}"
MULTIPART = "multipart/form-data"


def document_report_body(openapi: dict[str, Any]) -> dict[str, Any]:
    """Post-traitement de `app.openapi()` (posé par `create_app`) : publie `ReportMeta` et
    ses schémas (`ReportConsent`, `HeapSize`, `WasteType`) dans `components.schemas`, fait
    pointer le champ `meta` du corps multipart vers `ReportMeta` (envoyé en JSON :
    `encoding.meta.contentType`) et décrit la photo en binaire (`format: binary`).

    Modifie et renvoie le même dictionnaire. Sans la route (application de test), rien ne
    change."""
    operation = openapi.get("paths", {}).get(REPORTS_PATH, {}).get("post")
    if operation is None:
        return openapi
    schemas = openapi.setdefault("components", {}).setdefault("schemas", {})
    meta_schema = ReportMeta.model_json_schema(ref_template=SCHEMA_REF)
    for name, definition in meta_schema.pop("$defs", {}).items():
        existing = schemas.setdefault(name, definition)
        if existing != definition:
            raise RuntimeError(f"OpenAPI : schéma {name} déjà publié sous une autre forme")
    schemas["ReportMeta"] = meta_schema

    content = operation["requestBody"]["content"][MULTIPART]
    body = schemas[content["schema"]["$ref"].rsplit("/", 1)[-1]]
    meta = body["properties"]["meta"]
    body["properties"]["meta"] = {
        "$ref": SCHEMA_REF.format(model="ReportMeta"),
        "description": meta.get("description", ""),
    }
    body["properties"]["photo"]["format"] = "binary"
    content["encoding"] = {"meta": {"contentType": "application/json"}}
    return openapi
