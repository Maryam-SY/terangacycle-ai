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
    UNSUPPORTED_MEDIA_TYPE = "unsupported_media_type"
    PHOTO_TOO_LARGE = "photo_too_large"
    PHOTO_TOO_MANY_PIXELS = "photo_too_many_pixels"
    PHOTO_UNREADABLE = "photo_unreadable"
    STORAGE_UNAVAILABLE = "storage_unavailable"
    # Principal (core.security) et création d'un Signalement (story 1.11).
    INVALID_DEVICE_ID = "invalid_device_id"
    INVALID_TOKEN = "invalid_token"  # noqa: S105 (code d'erreur, pas un secret)
    CONSENT_REQUIRED = "consent_required"
    OUTSIDE_ACTIVE_ZONE = "outside_active_zone"


DEFAULT_MESSAGES: dict[ErrorCode, str] = {
    ErrorCode.NOT_FOUND: "Ressource introuvable.",
    ErrorCode.METHOD_NOT_ALLOWED: "Méthode non autorisée pour cette ressource.",
    ErrorCode.VALIDATION_ERROR: "La requête est invalide. Vérifiez les champs envoyés.",
    ErrorCode.INTERNAL_ERROR: "Erreur interne. Réessayez dans quelques instants.",
    ErrorCode.UNSUPPORTED_MEDIA_TYPE: (
        "Format de photo non pris en charge (JPEG, PNG ou WebP seulement). Reprenez la photo."
    ),
    ErrorCode.PHOTO_TOO_LARGE: "Photo trop lourde (1 Mo au plus). Reprenez la photo.",
    ErrorCode.PHOTO_TOO_MANY_PIXELS: (
        "Photo trop grande (12 mégapixels au plus). Reprenez la photo."
    ),
    ErrorCode.PHOTO_UNREADABLE: "Photo illisible ou abîmée. Reprenez la photo.",
    ErrorCode.STORAGE_UNAVAILABLE: "Stockage des photos indisponible. Réessayez plus tard.",
    # Story 1.11 : même texte que `errors.<code>` de web/src/i18n/fr.json (test).
    ErrorCode.INVALID_DEVICE_ID: (
        "Votre appareil n'a pas pu être reconnu. Fermez puis rouvrez l'application, et réessayez."
    ),
    ErrorCode.INVALID_TOKEN: "Votre session n'est plus valide. Reconnectez-vous puis réessayez.",
    ErrorCode.CONSENT_REQUIRED: (
        "Pour envoyer un signalement, acceptez d'abord les conditions d'utilisation."
    ),
    ErrorCode.OUTSIDE_ACTIVE_ZONE: (
        "TerangaCycle n'est pas encore actif ici. Merci de votre aide : vous pourrez signaler "
        "un dépôt dès que vous serez dans la zone couverte."
    ),
}


def default_message(code: str) -> str:
    """Message par défaut d'un code ; le code lui-même s'il n'en a pas."""
    try:
        return DEFAULT_MESSAGES[ErrorCode(code)]
    except ValueError:
        return code
