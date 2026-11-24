"""Worker arq (AD-8, AD-18) : même image que l'API.

Lancement : `arq app.worker.WorkerSettings`. Les tâches métier et les `cron_jobs`
arrivent avec leurs stories ; `noop` vérifie seulement la chaîne de bout en bout.
"""

from typing import Any, ClassVar

from arq.connections import RedisSettings

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger

log = get_logger(__name__)


async def noop(ctx: dict[str, Any]) -> None:
    """Tâche vide, sans effet."""
    log.info("noop")


async def startup(ctx: dict[str, Any]) -> None:
    configure_logging(get_settings().log_level)
    log.info("worker_started")


class WorkerSettings:
    functions: ClassVar[list] = [noop]
    on_startup = startup
    redis_settings = RedisSettings.from_dsn(get_settings().valkey_url)
