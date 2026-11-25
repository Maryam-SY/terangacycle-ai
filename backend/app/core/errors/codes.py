"""Codes d'erreur de l'API (AD-11) : énumération unique, exportée dans l'OpenAPI.

Chaque code a un message par défaut en français ; la PWA affiche sa propre
traduction (`errors.<code>` dans `web/src/i18n/fr.json` et `wo.json`, exigée par
`tests/unit/test_error_messages.py`). Les stories ajoutent leurs codes ici, jamais
ailleurs.
"""

from enum import StrEnum


class ErrorCode(StrEnum):
    NOT_FOUND = "not_found"
    METHOD_NOT_ALLOWED = "method_not_allowed"
    VALIDATION_ERROR = "validation_error"
    INTERNAL_ERROR = "internal_error"


DEFAULT_MESSAGES: dict[ErrorCode, str] = {
    ErrorCode.NOT_FOUND: "Ressource introuvable.",
    ErrorCode.METHOD_NOT_ALLOWED: "Méthode non autorisée pour cette ressource.",
    ErrorCode.VALIDATION_ERROR: "La requête est invalide. Vérifiez les champs envoyés.",
    ErrorCode.INTERNAL_ERROR: "Erreur interne. Réessayez dans quelques instants.",
}


def default_message(code: str) -> str:
    """Message par défaut d'un code ; le code lui-même s'il n'en a pas."""
    try:
        return DEFAULT_MESSAGES[ErrorCode(code)]
    except ValueError:
        return code
