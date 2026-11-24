"""Middleware de requête : `request_id`, journal d'accès et métriques Prometheus.

Pour chaque requête HTTP :
- un `request_id` (UUID4) est généré par le serveur, jamais repris du client, gardé
  dans `scope["state"]` et le contexte structlog, et renvoyé dans `X-Request-ID` ;
- une ligne de journal JSON : `request_id`, `route` (gabarit, jamais le chemin réel),
  `method`, `status`, `role` (`anonymous` tant qu'aucun principal n'est posé),
  `duration_ms` ; ni chemin, ni paramètres, ni en-têtes ;
- les compteurs et l'histogramme de `/metrics` ;
- une exception imprévue devient une réponse 500 `internal_error`, sans trace dans le
  corps, avec la trace complète dans le journal.
"""

import time
import uuid
from typing import Any

import structlog
from prometheus_client import Counter, Histogram
from starlette.routing import Match
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import ErrorCode, error_response
from app.core.logging import get_logger

log = get_logger("app.access")

REQUEST_ID_HEADER = "X-Request-ID"
# Libellé des requêtes sans route (404) : borne la cardinalité des métriques.
UNMATCHED_ROUTE = "<unmatched>"
# Méthodes connues ; toute autre (inventée par le client) devient OTHER dans les métriques.
KNOWN_METHODS = frozenset({"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"})
# Sondes appelées en boucle (healthchecks, Prometheus) : journal d'accès en DEBUG.
PROBE_ROUTES = frozenset({"/healthz", "/readyz", "/metrics"})

HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Requêtes HTTP traitées, par route, méthode et statut.",
    ["route", "method", "status"],
)
HTTP_DURATION = Histogram(
    "http_request_duration_seconds",
    "Durée de traitement des requêtes HTTP, par route et méthode.",
    ["route", "method"],
)


def _route_template(scope: Scope) -> str:
    """Gabarit de la route servie (`/v1/reports/{id}`), jamais le chemin réel."""
    route = scope.get("route")
    if route is None:
        # Routes Starlette (documentation OpenAPI) : FastAPI ne pose `route` que pour les
        # siennes. On retrouve le gabarit par correspondance ; PARTIAL = mauvaise méthode.
        partial = None
        for candidate in getattr(getattr(scope.get("app"), "router", None), "routes", []):
            match, _ = candidate.matches(scope)
            if match is Match.FULL:
                route = candidate
                break
            if match is Match.PARTIAL and partial is None:
                partial = candidate
        route = route or partial
    return getattr(route, "path_format", None) or getattr(route, "path", None) or UNMATCHED_ROUTE


class RequestContextMiddleware:
    """Middleware ASGI pur (pas de BaseHTTPMiddleware : contextvars et flux préservés)."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())
        state: dict[str, Any] = scope.setdefault("state", {})
        state["request_id"] = request_id
        status = 500
        response_started = False

        async def send_wrapper(message: Message) -> None:
            nonlocal status, response_started
            if message["type"] == "http.response.start":
                response_started = True
                status = message["status"]
                headers = list(message.get("headers", []))
                headers.append((REQUEST_ID_HEADER.lower().encode(), request_id.encode()))
                message = {**message, "headers": headers}
            await send(message)

        start = time.perf_counter()
        with structlog.contextvars.bound_contextvars(request_id=request_id):
            try:
                await self.app(scope, receive, send_wrapper)
            except Exception:
                log.exception("unhandled_exception", request_id=request_id)
                if response_started:
                    raise
                response = error_response(500, ErrorCode.INTERNAL_ERROR, request_id)
                await response(scope, receive, send_wrapper)
            finally:
                duration = time.perf_counter() - start
                route = _route_template(scope)
                method = scope["method"] if scope["method"] in KNOWN_METHODS else "OTHER"
                HTTP_REQUESTS.labels(route=route, method=method, status=str(status)).inc()
                HTTP_DURATION.labels(route=route, method=method).observe(duration)
                write = log.debug if route in PROBE_ROUTES else log.info
                write(
                    "request",
                    request_id=request_id,
                    route=route,
                    method=method,
                    status=status,
                    role=state.get("role", "anonymous"),
                    duration_ms=round(duration * 1000, 2),
                )
