"""Configuration publique de l'instance : `GET /v1/config` (AD-14).

Route publique (liste blanche d'AD-9), sans en-tête requis. Les stories suivantes y
ajoutent leurs champs publics sans changer la route.

La Zone active est chargée une fois, au démarrage de l'API (`app.state.active_zone`,
voir `app.main`) : la route ne touche pas la base.
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.core.config import Settings
from app.core.enums import Env
from app.core.geo import ActiveZone

router = APIRouter(prefix="/v1")


class PublicConfig(BaseModel):
    demo_mode: bool
    env: Env
    # None tant qu'aucun Modèle n'est livré.
    model_version: str | None
    # Polygone simplifié et élargi de 50 m : la PWA juge de façon tolérante, le serveur
    # tranche exactement à la création du Signalement.
    active_zone: ActiveZone
    # Au-delà (en mètres), la PWA invite à patienter ; exactement ce seuil : pas d'invitation.
    report_accuracy_flag_m: int


@router.get("/config", tags=["config"])
async def get_public_config(request: Request) -> PublicConfig:
    settings: Settings = request.app.state.settings
    return PublicConfig(
        demo_mode=settings.demo_mode,
        env=settings.env,
        model_version=settings.model_version,
        active_zone=request.app.state.active_zone,
        report_accuracy_flag_m=settings.report_accuracy_flag_m,
    )
