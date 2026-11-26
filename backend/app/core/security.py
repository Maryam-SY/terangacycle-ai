"""Principal unique de la requête (AD-9) : seul lecteur de `Authorization` et `X-Device-Id`.

Story 1.11 : seul le principal appareil existe (Citoyen anonyme). Tant qu'aucun jeton
n'est émis (epic 2), tout en-tête `Authorization` est invérifiable : 401 `invalid_token`.

`X-Device-Id` = 32 octets aléatoires en base64url sans remplissage (43 caractères),
générés par la PWA au premier lancement. Le serveur n'en garde que l'empreinte
`device_hash = HMAC-SHA256(DEVICE_ID_PEPPER, id)` : l'identifiant brut n'est jamais
stocké, journalisé ni renvoyé.
"""

import base64
import binascii
import hashlib
import hmac
import re
from dataclasses import dataclass
from typing import Annotated, Literal

from fastapi import Depends, Request

from app.core.config import Settings
from app.core.errors import DomainError, ErrorCode

DEVICE_ID_HEADER = "x-device-id"
_DEVICE_ID_CHARS = re.compile(r"[A-Za-z0-9_-]{43}")


@dataclass(frozen=True)
class Principal:
    """Auteur d'une requête. `owner_key` est immuable et jamais renvoyé hors du Personnel."""

    kind: Literal["device"]
    device_hash: str
    owner_key: str
    user_id: None = None
    role: None = None


def is_valid_device_id(raw: str) -> bool:
    """43 caractères base64url qui décodent exactement 32 octets (forme canonique)."""
    if not _DEVICE_ID_CHARS.fullmatch(raw):
        return False
    try:
        decoded = base64.urlsafe_b64decode(raw + "=")
    except (binascii.Error, ValueError):
        return False
    # Forme canonique : les 2 bits de remplissage du dernier caractère sont nuls.
    return len(decoded) == 32 and base64.urlsafe_b64encode(decoded).rstrip(b"=") == raw.encode()


def device_hash(device_id: str, pepper: str) -> str:
    """Empreinte HMAC-SHA256 de l'Identifiant d'appareil, en hexadécimal (64 caractères)."""
    return hmac.new(pepper.encode(), device_id.encode(), hashlib.sha256).hexdigest()


def resolve_principal(
    authorization: str | None, device_id: str | None, settings: Settings
) -> Principal:
    """Principal à partir des en-têtes ; lève 401 `invalid_token` ou 400 `invalid_device_id`."""
    if authorization is not None:
        raise DomainError(ErrorCode.INVALID_TOKEN, 401)
    if device_id is None or not is_valid_device_id(device_id):
        raise DomainError(ErrorCode.INVALID_DEVICE_ID, 400)
    if settings.device_id_pepper is None:
        raise RuntimeError("DEVICE_ID_PEPPER absent.")
    digest = device_hash(device_id, settings.device_id_pepper.get_secret_value())
    return Principal(kind="device", device_hash=digest, owner_key=f"device:{digest}")


def principal(request: Request) -> Principal:
    """Dépendance FastAPI : principal de la requête, résolu avant la validation du corps."""
    return resolve_principal(
        request.headers.get("authorization"),
        request.headers.get(DEVICE_ID_HEADER),
        request.app.state.settings,
    )


CurrentPrincipal = Annotated[Principal, Depends(principal)]
