"""Mise en file des tâches arq après le commit (AD-8, AD-17 ; story 1.18).

Seul chemin de l'application vers la file : `enqueue_after_commit(function, *args,
job_id=...)` enregistre la mise en file par `after_commit` dans l'unité de travail en
cours. Rien n'est donc mis en file si l'unité est annulée, ni si l'appelant n'a rien écrit
(il n'appelle pas cette fonction). `job_id` rend la tâche unique : arq refuse une seconde
tâche du même identifiant tant que la première, ou son résultat, est dans Valkey.

Utilisable depuis les deux sortes d'unité de travail (comme `core.storage._register`) :

- unité asynchrone (boucle asyncio) : la mise en file est une coroutine exécutée par la
  boucle après le commit ;
- unité synchrone : depuis un thread de travail anyio (route `def` de FastAPI), la
  coroutine est confiée à la boucle de l'application (`anyio.from_thread.run`) ; ailleurs
  (script, thread sans boucle), elle tourne dans une boucle éphémère (`asyncio.run`).

Chaque mise en file ouvre un pool arq éphémère, sans boucle de reconnexion, et dure au
plus `ENQUEUE_TIMEOUT_S` secondes. Valkey injoignable : l'échec est journalisé
(`job_enqueue_failed`, avec le seul `job_id`) et rien d'autre ne change, ni le commit déjà
fait ni la réponse.
"""

import asyncio
import math
from typing import Any

import anyio.from_thread
from anyio import NoEventLoopError
from arq.connections import RedisSettings, create_pool

from app.core.config import get_settings
from app.core.db import _require_uow, after_commit
from app.core.logging import get_logger

log = get_logger(__name__)

# Durée maximale d'une mise en file (connexion à Valkey comprise).
ENQUEUE_TIMEOUT_S = 2.0


def _redis_settings() -> RedisSettings:
    settings = RedisSettings.from_dsn(get_settings().valkey_url)
    # Un seul essai de connexion, au délai borné : aucune boucle de reconnexion d'arq.
    settings.conn_timeout = max(1, math.ceil(ENQUEUE_TIMEOUT_S))
    settings.conn_retries = 0
    return settings


async def _enqueue_once(function: str, args: tuple[Any, ...], job_id: str) -> None:
    pool = await create_pool(_redis_settings())
    try:
        job = await pool.enqueue_job(function, *args, _job_id=job_id)
    finally:
        await pool.aclose()
    if job is None:
        # Même `job_id` déjà en file, en cours ou terminé : rien de plus à faire.
        log.info("job_already_enqueued", job_id=job_id)
    else:
        log.info("job_enqueued", job_id=job_id)


async def _enqueue(function: str, args: tuple[Any, ...], job_id: str) -> None:
    """Met la tâche en file ; un échec est journalisé, jamais propagé."""
    try:
        await asyncio.wait_for(_enqueue_once(function, args, job_id), ENQUEUE_TIMEOUT_S)
    except Exception as exc:
        log.warning("job_enqueue_failed", job_id=job_id, reason=type(exc).__name__)


def _enqueue_blocking(function: str, args: tuple[Any, ...], job_id: str) -> None:
    """Mise en file depuis du code synchrone (effet d'une unité synchrone)."""
    try:
        anyio.from_thread.run(_enqueue, function, args, job_id)
        return
    except NoEventLoopError:
        # Pas un thread de travail anyio : aucune boucle à qui confier la coroutine.
        pass
    except Exception as exc:
        log.warning("job_enqueue_failed", job_id=job_id, reason=type(exc).__name__)
        return
    asyncio.run(_enqueue(function, args, job_id))


def enqueue_after_commit(function: str, *args: Any, job_id: str) -> None:
    """Met en file la tâche arq `function(*args)`, d'identifiant `job_id`, après le commit
    de l'unité de travail en cours ; jamais si elle est annulée.

    `RuntimeError` hors d'une unité de travail. Les arguments sont sérialisés par arq
    (pickle) : des valeurs simples (`str`, nombres).
    """
    if not job_id:
        raise ValueError("job_id est obligatoire : il rend la tâche unique.")
    if _require_uow().is_async:
        after_commit(_enqueue, function, args, job_id)
    else:
        after_commit(_enqueue_blocking, function, args, job_id)
