"""Outils partagés des tests de `POST /v1/reports` (story 1.11), unitaires et
d'intégration : Identifiants d'appareil, `meta` valide, envoi multipart."""

import base64
import json
import secrets
import uuid
from typing import Any

from starlette.types import ASGIApp

from tests import photos
from tests.asgi import Response, multipart, request

# Points de référence (latitude, longitude). Aucun n'est journalisé.
PLATEAU = (14.6708, -17.4381)  # Place de l'Indépendance, commune de Dakar-Plateau
THIES = (14.7910, -16.9359)  # Thiès, à 60 km : hors de la Zone active
# DEVICE_ID_PEPPER des tests : 32 octets en base64.
TEST_PEPPER = base64.b64encode(b"tc-test-device-id-pepper-1.11...").decode("ascii")
# Heure de l'appareil par défaut : passée pour toutes les horloges des tests (réelle, 2026,
# 2027, 2032), dans les bornes de `meta.captured_at`.
CAPTURED_AT = "2026-06-01T08:29:30+00:00"
# Valeur « absente » pour `report_meta()` : la clé est retirée.
MISSING: Any = object()
PATH = "/v1/reports"


def new_device_id() -> str:
    """Identifiant d'appareil valide : 32 octets aléatoires en base64url (43 caractères)."""
    return secrets.token_urlsafe(32)


def report_meta(**overrides: Any) -> dict[str, Any]:
    """`meta` valide au Plateau ; `champ=MISSING` retire le champ."""
    meta: dict[str, Any] = {
        "client_uuid": str(uuid.uuid4()),
        "lat": PLATEAU[0],
        "lng": PLATEAU[1],
        "accuracy_m": 12.5,
        "heap_size": "medium",
        "comment": "Tas de sacs près du marché",
        "waste_type": "plastic",
        "captured_at": CAPTURED_AT,
        "consent": {"terms": True, "training": False},
    }
    meta.update(overrides)
    return {key: value for key, value in meta.items() if value is not MISSING}


def sample_photo() -> bytes:
    """JPEG de 64 × 48, sans métadonnée."""
    return photos.encoded("JPEG", (64, 48))


def post_report(
    app: ASGIApp,
    device_id: str | None,
    meta: dict[str, Any] | str | None,
    photo: bytes | None,
    *,
    headers: dict[str, str] | None = None,
    filename: str = "depot.jpg",
    content_type: str = "image/jpeg",
) -> Response:
    """`POST /v1/reports` en multipart ; `None` omet l'en-tête, `meta` ou la photo."""
    fields = {}
    if meta is not None:
        fields["meta"] = meta if isinstance(meta, str) else json.dumps(meta, ensure_ascii=False)
    files = {"photo": (filename, photo, content_type)} if photo is not None else {}
    body, content_type_header = multipart(fields, files)
    all_headers = {"content-type": content_type_header, **(headers or {})}
    if device_id is not None:
        all_headers["X-Device-Id"] = device_id
    return request(app, "POST", PATH, body=body, headers=all_headers)
