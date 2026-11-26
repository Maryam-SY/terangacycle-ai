"""Worker arq (AD-8, AD-18) : même image que l'API.

Lancement : `arq app.worker.WorkerSettings`.

Battement : une tâche asyncio, lancée au démarrage dans le processus du worker, écrit
`worker:heartbeat` (horodatage Unix, TTL de 90 s) toutes les 15 s. Elle ne passe pas
par `cron_jobs` : une tâche planifiée transite par la file et serait retardée par une
file pleine, alors que la boucle prouve que le processus lui-même est vivant.
`/readyz` et le healthcheck Compose exigent un battement de moins de 60 s.

Healthcheck : `python -m app.worker healthcheck` (code 0 si le battement est frais).

Tâches métier : `thumb` (miniature d'une photo de Signalement, story 1.18), mise en file
par `reports.service` après le commit (`core.jobs`), d'identifiant `thumb:<photo_id>`. La
tâche délègue à `reports.service.make_thumbnail` dans le pool de threads ; stockage
indisponible : nouvel essai (`arq.Retry`) après un délai qui double, au plus
`THUMB_MAX_TRIES` essais, puis échec journalisé (`thumb_failed`). Les `cron_jobs`
arrivent avec leurs stories.
"""

import asyncio
import contextlib
import sys
from typing import Any, ClassVar
from uuid import UUID

from arq import Retry
from arq.connections import RedisSettings
from arq.worker import func
from redis.asyncio import Redis

from app.core.clock import now
from app.core.config import load_settings_or_exit
from app.core.errors import DomainError, ErrorCode
from app.core.health import HEARTBEAT_KEY, heartbeat_is_fresh
from app.core.logging import configure_logging, get_logger
from app.modules.reports import service as reports_service

log = get_logger(__name__)

HEARTBEAT_INTERVAL_S = 15
HEARTBEAT_TTL_S = 90
# Miniature : essais au plus (le premier compris), et délai avant le deuxième essai, qui
# double ensuite (5, 10, 20, 40 s).
THUMB_MAX_TRIES = 5
THUMB_RETRY_BASE_S = 5.0


async def noop(ctx: dict[str, Any]) -> None:
    """Tâche vide, sans effet."""
    log.info("noop")


async def thumb(ctx: dict[str, Any], photo_id: str) -> None:
    """Miniature de la photo `photo_id` (`reports.service.make_thumbnail`, pool de threads).

    Stockage indisponible : `Retry` après un délai croissant, jusqu'au `THUMB_MAX_TRIES`e
    essai, qui échoue (journal `thumb_failed`). Les journaux ne portent que `photo_id`.
    """
    job_try = int(ctx.get("job_try", 1))
    try:
        await asyncio.to_thread(reports_service.make_thumbnail, UUID(photo_id))
    except DomainError as exc:
        if exc.code is not ErrorCode.STORAGE_UNAVAILABLE:
            raise
        if job_try >= THUMB_MAX_TRIES:
            log.error("thumb_failed", photo_id=photo_id, job_try=job_try)
            # Exception simple : arq conserve le résultat sérialisé (pickle) de la tâche.
            raise RuntimeError(f"{exc.code.value} après {job_try} essais") from exc
        defer_s = THUMB_RETRY_BASE_S * 2 ** (job_try - 1)
        log.warning("thumb_retry", photo_id=photo_id, job_try=job_try, defer_s=defer_s)
        raise Retry(defer=defer_s) from exc


async def write_heartbeat(redis: Redis) -> None:
    await redis.set(HEARTBEAT_KEY, str(now().timestamp()), ex=HEARTBEAT_TTL_S)


async def heartbeat_loop(redis: Redis, interval_s: float = HEARTBEAT_INTERVAL_S) -> None:
    """Écrit le battement à intervalle fixe ; une erreur Valkey est journalisée, pas fatale."""
    while True:
        try:
            await write_heartbeat(redis)
        except Exception as exc:
            log.warning("heartbeat_failed", reason=type(exc).__name__)
        await asyncio.sleep(interval_s)


async def startup(ctx: dict[str, Any]) -> None:
    settings = load_settings_or_exit()
    configure_logging(settings.log_level)
    if settings.ephemeral_secrets:
        log.warning("ephemeral_secrets", secrets=list(settings.ephemeral_secrets))
    ctx["heartbeat_task"] = asyncio.create_task(heartbeat_loop(ctx["redis"]))
    log.info("worker_started")


async def shutdown(ctx: dict[str, Any]) -> None:
    task: asyncio.Task | None = ctx.pop("heartbeat_task", None)
    if task is not None:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
    log.info("worker_stopped")


class WorkerSettings:
    functions: ClassVar[list] = [
        noop,
        func(thumb, name=reports_service.THUMB_JOB, max_tries=THUMB_MAX_TRIES),
    ]
    # Tâches planifiées de l'épine (AD-18), ajoutées par leurs stories.
    cron_jobs: ClassVar[list] = []
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(load_settings_or_exit().valkey_url)


async def _healthcheck() -> bool:
    client = Redis.from_url(
        load_settings_or_exit().valkey_url, socket_connect_timeout=3, socket_timeout=3
    )
    try:
        return heartbeat_is_fresh(await client.get(HEARTBEAT_KEY))
    finally:
        await client.aclose()


def main(argv: list[str]) -> int:
    if argv != ["healthcheck"]:
        print("usage : python -m app.worker healthcheck", file=sys.stderr)
        return 2
    try:
        return 0 if asyncio.run(_healthcheck()) else 1
    except Exception as exc:
        print(f"healthcheck en échec : {type(exc).__name__}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
