"""Configuration publique de l'instance : `GET /v1/config` (AD-14).

Route publique (liste blanche d'AD-9), sans en-tête requis. Les stories suivantes y
ajoutent leurs champs publics (Zone active, seuil de précision) sans changer la route.
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.core.config import Settings
from app.core.enums import Env

router = APIRouter(prefix="/v1")


class PublicConfig(BaseModel):
    demo_mode: bool
    env: Env
    # None tant qu'aucun Modèle n'est livré.
    model_version: str | None


@router.get("/config", tags=["config"])
async def get_public_config(request: Request) -> PublicConfig:
    settings: Settings = request.app.state.settings
    return PublicConfig(
        demo_mode=settings.demo_mode, env=settings.env, model_version=settings.model_version
    )
