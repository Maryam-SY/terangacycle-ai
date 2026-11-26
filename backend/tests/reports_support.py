"""Outils des tests de `POST /v1/reports` : formulaire multipart, `meta` et appareil."""

import base64
import json
import uuid
from typing import Any

from fastapi import FastAPI

from tests.asgi import Response, request
from tests.photos import encode, noise

BOUNDARY = "----teranga-test-boundary"
# Place de l'Indépendance (Dakar-Plateau), dans la Zone active ; Thiès, hors Zone.
PLATEAU = (14.6708, -17.4381)
THIES = (14.7910, -16.9359)


def new_device_id() -> str:
    """Identifiant d'appareil valide : 32 octets aléatoires en base64url, 43 caractères."""
    return base64.urlsafe_b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes).rstrip(b"=").decode()


def small_jpeg() -> bytes:
    return encode(noise(64, 48), "JPEG", quality=80)


def meta(**overrides: Any) -> dict[str, Any]:
    """`meta` valide (Plateau, ± 12 m, tas moyen, conditions acceptées), modifiable."""
    lat, lng = PLATEAU
    value: dict[str, Any] = {
        "client_uuid": str(uuid.uuid4()),
        "lat": lat,
        "lng": lng,
        "accuracy_m": 12,
        "captured_at": "2026-11-26T09:30:00Z",
        "pile_size": "medium",
        "consent": {"terms": True, "training": False},
    }
    for key, item in overrides.items():
        if item is ...:
            value.pop(key, None)
        else:
            value[key] = item
    return value


def multipart(fields: dict[str, str], files: dict[str, tuple[str, bytes, str]]) -> bytes:
    """Corps `multipart/form-data` (champs texte, puis fichiers `nom → (fichier, octets, type)`)."""
    parts: list[bytes] = []
    for name, text_value in fields.items():
        parts.append(
            f'--{BOUNDARY}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
            + text_value.encode()
            + b"\r\n"
        )
    for name, (filename, data, content_type) in files.items():
        parts.append(
            (
                f"--{BOUNDARY}\r\nContent-Disposition: form-data; "
                f'name="{name}"; filename="{filename}"\r\n'
                f"Content-Type: {content_type}\r\n\r\n"
            ).encode()
            + data
            + b"\r\n"
        )
    return b"".join(parts) + f"--{BOUNDARY}--\r\n".encode()


def post_report(
    app: FastAPI,
    *,
    meta_value: dict[str, Any] | str | None = ...,  # type: ignore[assignment]
    photo: bytes | None = b"",
    device_id: str | None = "",
    extra_headers: dict[str, str] | None = None,
    voice: bytes | None = None,
) -> Response:
    """`POST /v1/reports`. Par défaut, tout est valide. `meta_value=None` ou `photo=None`
    omettent la partie ; `device_id=None` omet l'en-tête."""
    if meta_value is ...:
        meta_value = meta()
    fields: dict[str, str] = {}
    if meta_value is not None:
        fields["meta"] = meta_value if isinstance(meta_value, str) else json.dumps(meta_value)
    files: dict[str, tuple[str, bytes, str]] = {}
    if photo is not None:
        files["photo"] = ("depot.jpg", photo or small_jpeg(), "image/jpeg")
    if voice is not None:
        files["voice"] = ("note.webm", voice, "audio/webm")
    headers = {"content-type": f"multipart/form-data; boundary={BOUNDARY}"}
    if device_id is not None:
        headers["x-device-id"] = device_id or new_device_id()
    headers.update(extra_headers or {})
    return request(app, "POST", "/v1/reports", body=multipart(fields, files), headers=headers)


# En-tête EBML d'un conteneur WebM, suivi d'octets quelconques : assez pour le serveur, qui
# ne décode pas l'audio.
WEBM_VOICE = b"\x1a\x45\xdf\xa3" + b"\x00" * 2_000
