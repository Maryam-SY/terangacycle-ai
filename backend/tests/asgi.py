"""Client ASGI minimal pour les tests unitaires (sans httpx, absent des dépendances).

Appelle l'application directement, dans une boucle asyncio dédiée, et rassemble la
réponse. Le cycle de vie (lifespan) n'est pas exécuté.
"""

import asyncio
import json
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from starlette.types import ASGIApp, Message


@dataclass
class Response:
    status: int
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes = b""

    def json(self) -> Any:
        return json.loads(self.body)

    @property
    def text(self) -> str:
        return self.body.decode()


async def _call(
    app: ASGIApp,
    method: str,
    path: str,
    body: bytes,
    headers: dict[str, str],
    on_message: Callable[[Message], None] | None,
) -> Response:
    raw_path, _, query = path.partition("?")
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": raw_path,
        "raw_path": raw_path.encode(),
        "query_string": query.encode(),
        "root_path": "",
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        "client": ("127.0.0.1", 50000),
        "server": ("testserver", 80),
    }
    sent_body = False

    async def receive() -> Message:
        nonlocal sent_body
        if not sent_body:
            sent_body = True
            return {"type": "http.request", "body": body, "more_body": False}
        await asyncio.sleep(3600)
        return {"type": "http.disconnect"}

    response = Response(status=0)

    async def send(message: Message) -> None:
        if on_message is not None:
            on_message(message)
        if message["type"] == "http.response.start":
            response.status = message["status"]
            response.headers = {k.decode().lower(): v.decode() for k, v in message["headers"]}
        elif message["type"] == "http.response.body":
            response.body += message.get("body", b"")

    await app(scope, receive, send)
    return response


def request(
    app: ASGIApp,
    method: str,
    path: str,
    *,
    json_body: Any = None,
    body: bytes = b"",
    headers: dict[str, str] | None = None,
    on_message: Callable[[Message], None] | None = None,
) -> Response:
    """Requête de test ; `on_message` observe chaque message ASGI envoyé (ordre)."""
    headers = dict(headers or {})
    if json_body is not None:
        body = json.dumps(json_body).encode()
        headers.setdefault("content-type", "application/json")
    if body:
        headers.setdefault("content-length", str(len(body)))
    return asyncio.run(_call(app, method, path, body, headers, on_message))


def multipart(
    fields: dict[str, str], files: dict[str, tuple[str, bytes, str]]
) -> tuple[bytes, str]:
    """Corps `multipart/form-data` et son type de contenu.

    `fields` : champs texte ; `files` : nom → (nom de fichier, octets, type annoncé).
    """
    boundary = f"tc-test-{uuid.uuid4().hex}"
    crlf = b"\r\n"
    parts = [
        f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
        + value.encode("utf-8")
        + crlf
        for name, value in fields.items()
    ]
    parts += [
        (
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; '
            f'filename="{filename}"\r\nContent-Type: {content_type}\r\n\r\n'
        ).encode()
        + content
        + crlf
        for name, (filename, content, content_type) in files.items()
    ]
    body = b"".join(parts) + f"--{boundary}--\r\n".encode()
    return body, f"multipart/form-data; boundary={boundary}"
