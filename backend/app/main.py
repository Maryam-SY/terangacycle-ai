"""Point d'entrée HTTP : application FastAPI.

`create_app()` assemble les briques de `core` : gestionnaires d'erreurs, middleware
de requête, sondes, `/metrics` et `GET /v1/config`. Les routers des modules
arrivent avec leurs stories. Une configuration refusée arrête le processus (code 1).

Aucune application n'est créée à l'import : uvicorn appelle la fabrique
(`uvicorn --factory app.main:create_app`), les tests aussi.
"""

from fastapi import FastAPI

from app.core import health, public
from app.core.config import Settings, load_settings_or_exit
from app.core.enums import Env
from app.core.errors import ErrorResponse, install_error_handlers
from app.core.http import RequestContextMiddleware
from app.core.logging import configure_logging, get_logger

log = get_logger(__name__)


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
    )
    app.state.settings = settings

    install_error_handlers(app)
    app.add_middleware(RequestContextMiddleware)
    app.include_router(health.router)
    app.include_router(public.router)
    return app
