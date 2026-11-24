"""Journaux structurés en JSON via structlog, avec masquage des données sensibles.

Le processeur `mask_sensitive` (AD-10, AD-23) remplace par `"***"` la valeur de
toute clé sensible (téléphone, jeton, OTP, identifiant d'appareil, Position), à
tout niveau d'imbrication et sans tenir compte de la casse. Il s'applique aux
journaux structlog comme à ceux des bibliothèques (uvicorn, arq, SQLAlchemy).
"""

import logging
import sys
from collections.abc import Mapping
from typing import Any

import structlog

MASK = "***"

# Fragments sensibles, cherchés dans la clé normalisée (minuscules, `_` → `-`) :
# - fragments longs : en sous-chaîne (`phone_number`, `access_token`, `set-cookie`…) ;
# - fragments courts : seulement en segment entier entre `-` (`lat`, `start_lat`,
#   `otp_code`), pour ne pas masquer `platform`, `template` ou `latency_ms`.
SENSITIVE_FRAGMENTS: tuple[str, ...] = (
    "phone",
    "token",
    "device-id",
    "latitude",
    "longitude",
    "position",
    "location",
    "password",
    "secret",
    "pepper",
    "cookie",
    "authorization",
)
SENSITIVE_SEGMENTS: frozenset[str] = frozenset({"lat", "lng", "otp"})


def _is_sensitive(key: object) -> bool:
    if not isinstance(key, str):
        return False
    normalized = key.lower().replace("_", "-")
    if any(fragment in normalized for fragment in SENSITIVE_FRAGMENTS):
        return True
    return not SENSITIVE_SEGMENTS.isdisjoint(normalized.split("-"))


def _mask(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: MASK if _is_sensitive(k) else _mask(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_mask(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_mask(item) for item in value)
    return value


def mask_sensitive(
    _logger: Any, _method_name: str, event_dict: structlog.typing.EventDict
) -> structlog.typing.EventDict:
    """Processeur structlog : masque les valeurs des clés sensibles, récursivement."""
    return {k: MASK if _is_sensitive(k) else _mask(v) for k, v in event_dict.items()}


def _drop_color_message(
    _logger: Any, _method_name: str, event_dict: structlog.typing.EventDict
) -> structlog.typing.EventDict:
    # uvicorn ajoute en `extra` une copie colorée (ANSI) de son message.
    event_dict.pop("color_message", None)
    return event_dict


class _StdoutHandler(logging.StreamHandler):
    """Écrit sur le `sys.stdout` du moment (suit les redirections, dont celles des tests)."""

    @property  # type: ignore[override]
    def stream(self) -> Any:
        return sys.stdout

    @stream.setter
    def stream(self, _value: Any) -> None:
        pass


def configure_logging(level: str = "INFO") -> None:
    """Configure structlog et la bibliothèque standard pour une sortie JSON sur stdout."""
    log_level = logging.getLevelNamesMapping().get(level.upper(), logging.INFO)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        mask_sensitive,
    ]

    # structlog passe par la bibliothèque standard : un seul gestionnaire JSON (celui
    # de la racine) pour nos journaux comme pour ceux des bibliothèques (uvicorn, arq,
    # SQLAlchemy), remplacé à chaque appel.
    # Filtrage par le niveau de la bibliothèque standard (lu à chaque appel) : un
    # changement de niveau s'applique aussi aux loggers déjà mis en cache.
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    handler = _StdoutHandler()
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            # Champs `extra` des journaux standard inclus, donc masqués eux aussi.
            foreign_pre_chain=[
                structlog.stdlib.ExtraAdder(),
                _drop_color_message,
                *shared_processors,
            ],
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
        )
    )
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(log_level)

    # uvicorn et la commande arq posent leurs propres gestionnaires en texte brut :
    # on les retire pour que tout passe par le seul gestionnaire JSON de la racine.
    for name in ("uvicorn", "uvicorn.error", "arq"):
        library_logger = logging.getLogger(name)
        library_logger.handlers.clear()
        library_logger.propagate = True

    # Journal d'accès d'uvicorn coupé : il contient le chemin complet et ses paramètres
    # (Positions possibles). Le middleware de requête (core.http) le remplace.
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.handlers.clear()
    uvicorn_access.propagate = False


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
