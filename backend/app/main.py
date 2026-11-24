"""Point d'entrée HTTP : application FastAPI.

Aucune route pour l'instant ; les sondes et les conventions d'API arrivent avec la
story 1.2, les routers des modules avec leurs stories.
"""

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    return FastAPI(title="TerangaCycle AI", version="0.1.0")


app = create_app()
