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
    # Photo reçue (core.storage, story 1.10).
    PHOTO_TOO_LARGE = "photo_too_large"
    UNSUPPORTED_MEDIA_TYPE = "unsupported_media_type"
    PHOTO_TOO_MANY_PIXELS = "photo_too_many_pixels"
    PHOTO_UNREADABLE = "photo_unreadable"


DEFAULT_MESSAGES: dict[ErrorCode, str] = {
    ErrorCode.NOT_FOUND: "Ressource introuvable.",
    ErrorCode.METHOD_NOT_ALLOWED: "Méthode non autorisée pour cette ressource.",
    ErrorCode.VALIDATION_ERROR: "La requête est invalide. Vérifiez les champs envoyés.",
    ErrorCode.INTERNAL_ERROR: "Erreur interne. Réessayez dans quelques instants.",
    ErrorCode.PHOTO_TOO_LARGE: (
        "Cette photo est trop lourde. Reprenez-la depuis l'application, qui l'allège avant l'envoi."
    ),
    ErrorCode.UNSUPPORTED_MEDIA_TYPE: (
        "Ce fichier n'est pas une photo acceptée. "
        "Reprenez la photo avec l'appareil photo de l'application."
    ),
    ErrorCode.PHOTO_TOO_MANY_PIXELS: (
        "Cette photo est trop grande. "
        "Reprenez-la depuis l'application, qui la réduit avant l'envoi."
    ),
    ErrorCode.PHOTO_UNREADABLE: "Cette photo n'a pas pu être lue. Reprenez-la.",
}


def default_message(code: str) -> str:
    """Message par défaut d'un code ; le code lui-même s'il n'en a pas."""
    try:
        return DEFAULT_MESSAGES[ErrorCode(code)]
    except ValueError:
        return code
