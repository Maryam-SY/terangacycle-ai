"""Principal unique de l'API (AD-9, story 1.11).

Seul ce module lit les en-têtes d'identité. Avant l'Epic 2, le seul principal est
l'appareil du Citoyen anonyme :

- `X-Device-Id` : 32 octets aléatoires en base64url sans remplissage (43 caractères),
  générés par la PWA ; absent, répété ou d'une autre forme → 400 `invalid_device_id` ;
- `Authorization` : aucun jeton n'est vérifiable avant l'Epic 2 ; sa seule présence
  donne 401 `invalid_token` (jamais un repli silencieux sur l'appareil) ;
- les deux à la fois : 400 d'abord (l'appareil est contrôlé avant le jeton) ;
- `device_hash = HMAC-SHA256(DEVICE_ID_PEPPER, X-Device-Id)` en hexadécimal, et
  `owner_key = device:<device_hash>`.

La clé HMAC est décodée une fois, depuis les réglages avec lesquels l'application a été
construite (`app.state.settings`), et gardée dans `app.state.device_id_key`.

Confidentialité : ni l'Identifiant d'appareil, ni son empreinte, ni `owner_key` ne sont
journalisés ni renvoyés ; ils sont absents du `repr` du principal.
"""

import base64
import binascii
import hashlib
import hmac
import re
from dataclasses import dataclass, field
from typing import Any, Literal

from fastapi import Request
from starlette.datastructures import Headers

from app.core.config import Settings
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


def device_id_key(settings: Settings) -> bytes:
    """Clé HMAC des Identifiants d'appareil : DEVICE_ID_PEPPER décodé (base64 strict).

    Lève `InvalidPepperError` si le secret manque ou ne fait pas 32 octets au moins.
    """
    secret = settings.device_id_pepper
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


def app_device_id_key(state: Any) -> bytes:
    """Clé de l'application : posée au démarrage (lifespan), sinon décodée une fois depuis
    `state.settings` et gardée dans `state.device_id_key`."""
    key = getattr(state, "device_id_key", None)
    if key is None:
        key = device_id_key(state.settings)
        state.device_id_key = key
    return key


def device_hash(device_id: str, key: bytes) -> str:
    """Empreinte HMAC-SHA256 (hexadécimal) d'un Identifiant d'appareil déjà validé."""
    return hmac.new(key, device_id.encode("ascii"), hashlib.sha256).hexdigest()


def device_principal(device_id: str, key: bytes) -> Principal:
    hashed = device_hash(device_id, key)
    return Principal(kind="device", device_hash=hashed, owner_key=f"device:{hashed}")


def check_identity_headers(headers: Headers) -> str:
    """Identifiant d'appareil valide de la requête, ou `DomainError`.

    Ordre fixe : `X-Device-Id` absent, répété ou mal formé → 400 `invalid_device_id`,
    avant tout `Authorization` présent → 401 `invalid_token`. Utilisé par `principal()`
    et, avant toute lecture du corps, par la garde de `POST /v1/reports`.
    """
    device_ids = headers.getlist(DEVICE_ID_HEADER)
    if len(device_ids) != 1 or not DEVICE_ID_PATTERN.fullmatch(device_ids[0]):
        raise DomainError(ErrorCode.INVALID_DEVICE_ID, 400)
    if AUTHORIZATION_HEADER in headers:
        raise DomainError(ErrorCode.INVALID_TOKEN, 401)
    return device_ids[0]


def principal(request: Request) -> Principal:
    """Dépendance FastAPI : le principal de la requête, ou une erreur.

    `X-Device-Id` absent ou invalide → 400 `invalid_device_id`, contrôlé avant le jeton ;
    `Authorization` présent → 401 `invalid_token`. Pour `POST /v1/reports`, la même
    vérification a déjà eu lieu avant la lecture du corps (garde du router) ; un refus
    n'écrit jamais rien.
    """
    device_id = check_identity_headers(request.headers)
    found = device_principal(device_id, app_device_id_key(request.app.state))
    # Journal d'accès (core.http) : le type de principal, jamais son identité.
    request.state.role = found.kind
    return found
