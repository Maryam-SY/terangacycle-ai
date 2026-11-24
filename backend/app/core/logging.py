"""Journaux structurés en JSON via structlog.

Le masquage des données personnelles (AD-10, AD-23) arrive avec les stories qui
les manipulent.
"""

import logging
import sys

import structlog


def configure_logging(level: str = "INFO") -> None:
    """Configure structlog et la bibliothèque standard pour une sortie JSON sur stdout."""
    log_level = logging.getLevelNamesMapping().get(level.upper(), logging.INFO)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Les journaux des bibliothèques (uvicorn, arq, SQLAlchemy) sortent aussi en JSON.
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.JSONRenderer(),
            ],
        )
    )
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(log_level)

    # uvicorn et la commande arq posent leurs propres gestionnaires en texte brut :
    # on les retire pour que tout passe par le seul gestionnaire JSON de la racine.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "arq"):
        library_logger = logging.getLogger(name)
        library_logger.handlers.clear()
        library_logger.propagate = True


def get_logger(name: str | None = None) -> structlog.typing.FilteringBoundLogger:
    return structlog.get_logger(name)
