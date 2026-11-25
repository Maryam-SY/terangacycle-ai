"""Principal unique de l'API (AD-9, story 1.11).

Seule `principal()` lit les en-têtes d'identité. Avant l'Epic 2, le seul principal est
l'appareil du Citoyen anonyme :

- `X-Device-Id` : 32 octets aléatoires en base64url sans remplissage (43 caractères),
  générés par la PWA ; absent, répété ou d'une autre forme → 400 `invalid_device_id` ;
- `Authorization` : aucun jeton n'est vérifiable avant l'Epic 2 ; sa seule présence
  donne 401 `invalid_token` (jamais un repli silencieux sur l'appareil) ;
- `device_hash = HMAC-SHA256(DEVICE_ID_PEPPER, X-Device-Id)` en hexadécimal, et
  `owner_key = device:<device_hash>`.

Confidentialité : ni l'Identifiant d'appareil, ni son empreinte, ni `owner_key` ne sont
journalisés ni renvoyés ; ils sont absents du `repr` du principal.
"""

import base64
import binascii
import hashlib
import hmac
import re
from dataclasses import dataclass, field
from typing import Literal

from fastapi import Request

from app.core.config import Settings, get_settings
from app.core.errors import DomainError, ErrorCode

DEVICE_ID_HEADER = "x-device-id"
AUTHORIZATION_HEADER = "authorization"
# Même forme que `DEVICE_ID_PATTERN` de la PWA (web/src/offline/device.ts).
DEVICE_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{43}")
# DEVICE_ID_PEPPER : 32 octets aléatoires en base64 (inventaire d'AD-26).
DEVICE_ID_PEPPER_MIN_BYTES = 32

# `user` arrivera avec les comptes (Epic 2).
PrincipalKind = Literal["device"]


class InvalidPepperError(RuntimeError):
    """DEVICE_ID_PEPPER absent ou mal formé. Le message ne contient jamais sa valeur."""


@dataclass(frozen=True, slots=True)
class Principal:
    """Auteur d'une requête. `device_hash` et `owner_key` restent hors du `repr`."""

    kind: PrincipalKind
    device_hash: str = field(repr=False)
    owner_key: str = field(repr=False)


def device_id_key(settings: Settings | None = None) -> bytes:
    """Clé HMAC des Identifiants d'appareil : DEVICE_ID_PEPPER décodé (base64 strict).

    Lève `InvalidPepperError` si le secret manque ou ne fait pas 32 octets au moins.
    """
    secret = (settings or get_settings()).device_id_pepper
    if secret is None:
        raise InvalidPepperError("DEVICE_ID_PEPPER : secret absent")
    try:
        key = base64.b64decode(secret.get_secret_value().strip(), validate=True)
    except (binascii.Error, ValueError):
        raise InvalidPepperError("DEVICE_ID_PEPPER : base64 invalide") from None
    if len(key) < DEVICE_ID_PEPPER_MIN_BYTES:
        raise InvalidPepperError(
            f"DEVICE_ID_PEPPER : {DEVICE_ID_PEPPER_MIN_BYTES} octets au moins attendus"
        )
    return key


def device_hash(device_id: str, key: bytes) -> str:
    """Empreinte HMAC-SHA256 (hexadécimal) d'un Identifiant d'appareil déjà validé."""
    return hmac.new(key, device_id.encode("ascii"), hashlib.sha256).hexdigest()


def device_principal(device_id: str, key: bytes) -> Principal:
    hashed = device_hash(device_id, key)
    return Principal(kind="device", device_hash=hashed, owner_key=f"device:{hashed}")


def principal(request: Request) -> Principal:
    """Dépendance FastAPI : le principal de la requête, ou une erreur 400 ou 401.

    Contrôlée avant le corps de la requête : un refus n'écrit jamais rien.
    """
    device_ids = request.headers.getlist(DEVICE_ID_HEADER)
    if len(device_ids) != 1 or not DEVICE_ID_PATTERN.fullmatch(device_ids[0]):
        raise DomainError(ErrorCode.INVALID_DEVICE_ID, 400)
    if AUTHORIZATION_HEADER in request.headers:
        raise DomainError(ErrorCode.INVALID_TOKEN, 401)
    found = device_principal(device_ids[0], device_id_key())
    # Journal d'accès (core.http) : le type de principal, jamais son identité.
    request.state.role = found.kind
    return found
