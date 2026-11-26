"""Erreurs de l'API : `DomainError`, enveloppe unique et gestionnaires (AD-11).

Un service lève `DomainError` ; jamais de `HTTPException` dans un service. Toute
réponse d'erreur suit l'enveloppe `{"error": {"code", "message", "request_id"}}`,
sans trace ni détail interne ; la trace complète part dans le journal.
"""

import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.errors.codes import ErrorCode, default_message
from app.core.logging import get_logger

__all__ = [
    "DomainError",
    "field_name",
    "validation_error",
    "ErrorBody",
    "ErrorCode",
    "ErrorResponse",
    "error_response",
    "install_error_handlers",
    "request_id_of",
]

log = get_logger(__name__)


class DomainError(Exception):
    """Erreur métier portant un code de `ErrorCode` et le statut HTTP à renvoyer.

    Un code hors de l'énumération est refusé (`ValueError`) : chaque code est déclaré
    une fois dans `codes.py`, avec son message par défaut.
    """

    def __init__(self, code: ErrorCode | str, http_status: int, message: str | None = None) -> None:
        self.code = ErrorCode(code)
        self.http_status = http_status
        self.message = message or default_message(self.code)
        super().__init__(self.message)

    def __repr__(self) -> str:
        return f"DomainError(code={self.code.value!r}, http_status={self.http_status})"


class ErrorBody(BaseModel):
    code: ErrorCode
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    """Enveloppe unique de toute réponse d'erreur."""

    error: ErrorBody


# Statut HTTP → code, pour les HTTPException levées par Starlette (routage).
_STATUS_CODES: dict[int, ErrorCode] = {
    404: ErrorCode.NOT_FOUND,
    405: ErrorCode.METHOD_NOT_ALLOWED,
    422: ErrorCode.VALIDATION_ERROR,
}


def request_id_of(request: Request) -> str:
    """`request_id` posé par le middleware ; un nouveau s'il manque (hors middleware)."""
    request_id = request.scope.get("state", {}).get("request_id")
    return request_id or str(uuid.uuid4())


def error_response(
    status_code: int,
    code: str,
    request_id: str,
    message: str | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body = {
        "error": {
            "code": str(code),
            "message": message or default_message(code),
            "request_id": request_id,
        }
    }
    return JSONResponse(body, status_code=status_code, headers=headers)


def _code_for_status(status_code: int) -> ErrorCode:
    if status_code in _STATUS_CODES:
        return _STATUS_CODES[status_code]
    # Aucun autre statut n'est levé par HTTPException aujourd'hui (les services lèvent
    # DomainError) : 4xx inconnu → requête invalide, 5xx → erreur interne.
    return ErrorCode.INTERNAL_ERROR if status_code >= 500 else ErrorCode.VALIDATION_ERROR


async def _http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    # Le `detail` n'est jamais renvoyé : seul le message du code l'est. On garde les
    # en-têtes utiles (Allow pour 405, par exemple).
    return error_response(
        exc.status_code,
        _code_for_status(exc.status_code),
        request_id_of(request),
        headers=dict(exc.headers) if exc.headers else None,
    )


# Premier segment d'un emplacement d'erreur FastAPI : la partie de la requête, pas un champ.
_REQUEST_PARTS = {"body", "query", "path", "header", "cookie"}


def field_name(location: tuple[Any, ...] | list[Any], prefix: str = "") -> str:
    """Nom lisible d'un champ fautif (`photo`, `meta.consent.terms`) ; jamais sa valeur."""
    parts = [str(part) for part in location]
    if parts and parts[0] in _REQUEST_PARTS:
        parts = parts[1:]
    name = ".".join(parts)
    if prefix:
        return f"{prefix}.{name}" if name else prefix
    return name or "requête"


def validation_error(fields: list[str]) -> DomainError:
    """422 `validation_error` dont le message nomme les champs fautifs, sans leurs valeurs."""
    names = list(dict.fromkeys(fields))  # ordre gardé, sans doublon
    message = default_message(ErrorCode.VALIDATION_ERROR)
    if names:
        message = f"{message} Champs : {', '.join(names)}."
    return DomainError(ErrorCode.VALIDATION_ERROR, 422, message)


async def _validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    errors = exc.errors() if isinstance(exc, RequestValidationError) else []
    error = validation_error([field_name(item.get("loc", ())) for item in errors])
    return error_response(422, error.code, request_id_of(request), error.message)


async def _domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    return error_response(exc.http_status, exc.code, request_id_of(request), exc.message)


async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Filet de sécurité : le middleware de requête intercepte déjà les exceptions.
    request_id = request_id_of(request)
    log.error("unhandled_exception", request_id=request_id, exc_info=exc)
    return error_response(500, ErrorCode.INTERNAL_ERROR, request_id)


def install_error_handlers(app: FastAPI) -> None:
    handlers: dict[Any, Any] = {
        StarletteHTTPException: _http_exception_handler,
        RequestValidationError: _validation_exception_handler,
        DomainError: _domain_error_handler,
        Exception: _unhandled_exception_handler,
    }
    for exc_class, handler in handlers.items():
        app.add_exception_handler(exc_class, handler)
