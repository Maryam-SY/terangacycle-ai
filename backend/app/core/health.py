"""Sondes et métriques internes (AD-27) : `/healthz`, `/readyz`, `/metrics`.

- `/healthz` : vivacité du processus, sans aucune dépendance externe.
- `/readyz` : base (`SELECT 1`), Valkey (`PING`), bucket (`head_bucket`) et battement
  du worker (`worker:heartbeat` de moins de 60 s), vérifiés en parallèle avec un délai
  de 2 s chacun. Le corps ne donne que le statut global ; la cause part dans le journal.
- `/metrics` : format Prometheus, réseau interne seulement (jamais relayé par Caddy).
"""

import asyncio
import math
from collections.abc import Awaitable, Callable
from functools import lru_cache
from typing import Any

import boto3
from botocore.config import Config
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from redis.asyncio import Redis
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.pool import NullPool

from app.core.clock import now
from app.core.config import Settings
from app.core.logging import get_logger

log = get_logger(__name__)

HEARTBEAT_KEY = "worker:heartbeat"
HEARTBEAT_MAX_AGE_S = 60.0
# Tolérance d'horloge entre le worker et l'API : un battement « dans le futur » au-delà
# est refusé (horodatage faux ou horloge déréglée).
HEARTBEAT_CLOCK_SKEW_S = 5.0
CHECK_TIMEOUT_S = 2.0
# Délais S3 de la sonde : connexion + lecture tiennent dans CHECK_TIMEOUT_S.
S3_PROBE_TIMEOUT_S = 1

router = APIRouter()


# --- Battement du worker ----------------------------------------------------------


def heartbeat_age(raw: bytes | str | None) -> float | None:
    """Âge en secondes d'un battement (horodatage Unix), None s'il est absent ou illisible."""
    if raw is None:
        return None
    try:
        value = float(raw.decode() if isinstance(raw, bytes) else raw)
    except (UnicodeDecodeError, ValueError):
        return None
    return now().timestamp() - value


def heartbeat_is_fresh(raw: bytes | str | None) -> bool:
    """Vrai si le battement a moins de 60 s (ni infini, ni NaN, ni trop dans le futur)."""
    age = heartbeat_age(raw)
    return (
        age is not None
        and math.isfinite(age)
        and -HEARTBEAT_CLOCK_SKEW_S <= age < HEARTBEAT_MAX_AGE_S
    )


# --- Vérifications de /readyz ----------------------------------------------------
# Chacune lève une exception si la dépendance n'est pas prête.


def _redis(settings: Settings) -> Redis:
    return Redis.from_url(
        settings.valkey_url,
        socket_connect_timeout=CHECK_TIMEOUT_S,
        socket_timeout=CHECK_TIMEOUT_S,
    )


@lru_cache
def _s3_session() -> boto3.session.Session:
    # Session dédiée : la session par défaut de boto3 n'est pas sûre entre threads.
    return boto3.session.Session()


@lru_cache
def _s3_client(endpoint: str, region: str, access_key: str, secret_key: str) -> Any:
    # Configuration explicite pour Garage (AD-13) : path-style, sommes de contrôle
    # seulement si exigées, délais d'une seconde et aucun nouvel essai pour une sonde.
    return _s3_session().client(
        "s3",
        endpoint_url=endpoint,
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
            connect_timeout=S3_PROBE_TIMEOUT_S,
            read_timeout=S3_PROBE_TIMEOUT_S,
            retries={"total_max_attempts": 1, "mode": "standard"},
        ),
    )


@lru_cache
def _probe_engine(url: str) -> Engine:
    """Moteur réservé à la sonde : connexion neuve, délais bornés à 2 s (connexion et requête).

    Aucun pool : une base en panne ne laisse ni connexion ni thread bloqué au-delà du délai.
    """
    return create_engine(
        url,
        poolclass=NullPool,
        connect_args={
            "connect_timeout": int(CHECK_TIMEOUT_S),
            "options": f"-c statement_timeout={int(CHECK_TIMEOUT_S * 1000)}",
        },
    )


def _select_one(settings: Settings) -> None:
    if settings.database_url is None:
        raise RuntimeError("base non configurée")
    with _probe_engine(settings.database_url.get_secret_value()).connect() as conn:
        conn.execute(text("SELECT 1"))


async def check_database(settings: Settings) -> None:
    await asyncio.to_thread(_select_one, settings)


async def check_valkey(settings: Settings) -> None:
    client = _redis(settings)
    try:
        if not await client.ping():
            raise RuntimeError("PING sans réponse")
    finally:
        await client.aclose()


def _head_bucket(settings: Settings) -> None:
    if settings.s3_access_key_id is None or settings.s3_secret_access_key is None:
        raise RuntimeError("identifiants S3 absents")
    client = _s3_client(
        settings.s3_endpoint,
        settings.s3_region,
        settings.s3_access_key_id.get_secret_value(),
        settings.s3_secret_access_key.get_secret_value(),
    )
    client.head_bucket(Bucket=settings.s3_bucket)


async def check_storage(settings: Settings) -> None:
    await asyncio.to_thread(_head_bucket, settings)


async def check_worker(settings: Settings) -> None:
    client = _redis(settings)
    try:
        raw = await client.get(HEARTBEAT_KEY)
    finally:
        await client.aclose()
    if not heartbeat_is_fresh(raw):
        raise RuntimeError("battement du worker absent ou trop ancien")


Check = Callable[[Settings], Awaitable[None]]

# Nom → vérification ; les tests remplacent les entrées pour simuler une panne.
READINESS_CHECKS: dict[str, Check] = {
    "database": check_database,
    "valkey": check_valkey,
    "storage": check_storage,
    "worker": check_worker,
}


async def _run_check(name: str, check: Check, settings: Settings) -> bool:
    try:
        await asyncio.wait_for(check(settings), timeout=CHECK_TIMEOUT_S)
    except TimeoutError:
        log.warning("readiness_check_failed", check=name, reason="timeout")
        return False
    except Exception as exc:
        # Cause dans le journal seulement (type d'exception, sans message : il peut
        # contenir une URL ou un identifiant).
        log.warning("readiness_check_failed", check=name, reason=type(exc).__name__)
        return False
    return True


async def readiness(settings: Settings) -> bool:
    results = await asyncio.gather(
        *(_run_check(name, check, settings) for name, check in READINESS_CHECKS.items())
    )
    return all(results)


# --- Routes -----------------------------------------------------------------------


@router.get("/healthz", tags=["sondes"])
async def healthz() -> dict[str, str]:
    """Vivacité : 200 tant que le processus répond, sans aucune dépendance."""
    return {"status": "ok"}


@router.get(
    "/readyz",
    tags=["sondes"],
    responses={503: {"description": "Une dépendance n'est pas prête (aucun détail)."}},
)
async def readyz(request: Request) -> JSONResponse:
    """Prêt : base, Valkey, bucket et battement du worker répondent."""
    if await readiness(request.app.state.settings):
        return JSONResponse({"status": "ready"})
    return JSONResponse({"status": "not_ready"}, status_code=503)


@router.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    """Métriques Prometheus ; interne au réseau Compose (Caddy ne la relaie pas)."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
