"""Erreurs de l'API : `DomainError`, enveloppe unique et gestionnaires (AD-11).

Un service lève `DomainError` ; jamais de `HTTPException` dans un service. Toute
réponse d'erreur suit l'enveloppe `{"error": {"code", "message", "request_id"}}`,
sans trace ni détail interne ; la trace complète part dans le journal.

Une requête invalide (422 `validation_error`) nomme les champs fautifs dans son message,
jamais leur valeur : `validation_error(["meta.lat"])` ou la validation de FastAPI.
"""

import re
import uuid
from collections.abc import Iterable, Sequence
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
    "ErrorBody",
    "ErrorCode",
    "ErrorResponse",
    "error_response",
    "field_of",
    "install_error_handlers",
    "request_id_of",
    "validation_error",
    "validation_message",
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


# Champs nommés dans le message d'une erreur de validation : noms seulement, jamais une
# valeur reçue ; un nom fourni par le client (clé inconnue) est assaini et borné.
MAX_NAMED_FIELDS = 5
MAX_FIELD_NAME_LENGTH = 64
_UNSAFE_FIELD_CHARS = re.compile(r"[^A-Za-z0-9_.\-]")
# Premier élément de `loc` dans une erreur de FastAPI : la source, pas le champ.
_REQUEST_SOURCES = frozenset({"body", "query", "path", "header", "cookie"})


def _safe_field_name(name: str) -> str:
    return _UNSAFE_FIELD_CHARS.sub("?", name)[:MAX_FIELD_NAME_LENGTH] or "?"


def validation_message(fields: Iterable[str]) -> str:
    """Message d'une requête invalide qui nomme les champs à vérifier (5 au plus)."""
    names = list(dict.fromkeys(_safe_field_name(name) for name in fields))
    if not names:
        return default_message(ErrorCode.VALIDATION_ERROR)
    label = "Champ à vérifier" if len(names) == 1 else "Champs à vérifier"
    shown = ", ".join(names[:MAX_NAMED_FIELDS])
    more = " …" if len(names) > MAX_NAMED_FIELDS else ""
    return f"La requête est invalide. {label} : {shown}{more}."


def validation_error(fields: Iterable[str]) -> DomainError:
    """422 `validation_error` dont le message nomme les champs fautifs."""
    return DomainError(ErrorCode.VALIDATION_ERROR, 422, validation_message(fields))


def field_of(loc: Sequence[Any], prefix: str | None = None) -> str:
    """Nom pointé d'un champ d'après le `loc` d'une erreur de validation.

    Erreur de FastAPI : la source est retirée, `("body", "photo")` → `photo`. Erreur d'un
    modèle reçu dans un champ : `("consent", "terms")` avec `prefix="meta"` →
    `meta.consent.terms` ; un `loc` vide désigne le champ lui-même (`meta`).
    """
    parts = [str(part) for part in loc]
    if prefix is not None:
        return ".".join([prefix, *parts])
    if len(parts) > 1 and parts[0] in _REQUEST_SOURCES:
        parts = parts[1:]
    return ".".join(parts) or "?"


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


async def _validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    errors = exc.errors() if isinstance(exc, RequestValidationError) else []
    # JSON illisible : le `loc` porte une position dans le corps, pas un champ.
    fields = [
        "body" if error.get("type") == "json_invalid" else field_of(error.get("loc", ()))
        for error in errors
    ]
    return error_response(
        422, ErrorCode.VALIDATION_ERROR, request_id_of(request), validation_message(fields)
    )


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
