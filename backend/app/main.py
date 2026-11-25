"""Point d'entrée HTTP : application FastAPI.

`create_app()` assemble les briques de `core` : gestionnaires d'erreurs, middleware
de requête, sondes, `/metrics` et `GET /v1/config`, puis les routers des modules
(`reports` depuis la story 1.11). Une configuration refusée arrête le processus (code 1).

Au démarrage (lifespan), l'API vérifie la clé DEVICE_ID_PEPPER (32 octets en base64,
AD-26) puis charge la Zone active une fois (`app.state.active_zone`). Clé mal formée,
Zone inconnue ou base injoignable : journal `startup_refused` et code de sortie 1.

Aucune application n'est créée à l'import : uvicorn appelle la fabrique
(`uvicorn --factory app.main:create_app`), les tests aussi (sans lifespan : ils posent
eux-mêmes `app.state.active_zone`).
"""

import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import NoReturn

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool
from starlette.concurrency import run_in_threadpool

from app.core import health, public, security
from app.core.config import Settings, load_settings_or_exit
from app.core.enums import Env
from app.core.errors import ErrorResponse, install_error_handlers
from app.core.geo import ActiveZone, UnknownZoneError, load_active_zone
from app.core.http import RequestContextMiddleware
from app.core.logging import configure_logging, get_logger
from app.modules.reports import router as reports_router

log = get_logger(__name__)

# Délais au démarrage (connexion, requête) : une base arrêtée ou bloquée refuse vite.
STARTUP_DB_TIMEOUT_S = 5
# SQLSTATE PostgreSQL traduits en raison lisible (jamais le message du pilote).
STARTUP_SQLSTATE_REASONS = {
    "42P01": "table zones absente : migration 0002 non appliquée",
    "42501": "droit de lecture manquant sur zones",
}


def read_active_zone(settings: Settings) -> ActiveZone:
    """Zone active lue en base, par une connexion dédiée et fermée aussitôt."""
    if settings.database_url is None:
        raise RuntimeError("base non configurée")
    engine = create_engine(
        settings.database_url.get_secret_value(),
        poolclass=NullPool,
        # Les paramètres ne figurent jamais dans les messages d'erreur.
        hide_parameters=True,
        connect_args={
            "connect_timeout": STARTUP_DB_TIMEOUT_S,
            "options": f"-c statement_timeout={STARTUP_DB_TIMEOUT_S * 1000}",
        },
    )
    try:
        with Session(engine) as session:
            return load_active_zone(session, settings.active_zone_id)
    finally:
        engine.dispose()


def refuse_startup(reason: str) -> NoReturn:
    """Journal `startup_refused`, puis fin du processus avec le code 1.

    `os._exit` plutôt que `SystemExit` : uvicorn transforme l'échec d'un lifespan en code
    de sortie 3. Rien n'est encore servi à ce stade : il n'y a rien d'autre à fermer.
    """
    log.critical("startup_refused", reason=reason)
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(1)


def load_active_zone_or_exit(settings: Settings) -> ActiveZone:
    try:
        return read_active_zone(settings)
    except UnknownZoneError:
        reason = "ACTIVE_ZONE_ID : aucune Zone ne porte cet identifiant"
    except DBAPIError as exc:
        sqlstate = getattr(exc.orig, "sqlstate", None)
        reason = STARTUP_SQLSTATE_REASONS.get(
            sqlstate or "", f"base injoignable ou illisible ({type(exc).__name__})"
        )
    except Exception as exc:
        # Seul le type : le message d'un pilote peut contenir l'URL de la base.
        reason = f"base injoignable ou illisible ({type(exc).__name__})"
    refuse_startup(reason)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    try:
        security.device_id_key(settings)
    except security.InvalidPepperError as exc:
        # Le message nomme le secret, jamais sa valeur.
        refuse_startup(str(exc))
    app.state.active_zone = await run_in_threadpool(load_active_zone_or_exit, settings)
    log.info("active_zone_loaded", zone=app.state.active_zone.id)
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings_or_exit()
    configure_logging(settings.log_level)
    if settings.ephemeral_secrets:
        log.warning("ephemeral_secrets", secrets=list(settings.ephemeral_secrets))

    # AD-23 : documentation OpenAPI absente en production.
    docs_enabled = settings.env is not Env.PROD
    app = FastAPI(
        title="TerangaCycle AI",
        version="0.1.0",
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
        # Toute erreur suit l'enveloppe unique (exportée dans l'OpenAPI avec ErrorCode).
        responses={"default": {"model": ErrorResponse, "description": "Enveloppe d'erreur"}},
        lifespan=lifespan,
    )
    app.state.settings = settings

    install_error_handlers(app)
    app.add_middleware(RequestContextMiddleware)
    app.include_router(health.router)
    app.include_router(public.router)
    app.include_router(reports_router.router)
    return app
