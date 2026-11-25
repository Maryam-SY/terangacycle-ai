"""Service du module orgs (AD-31).

`responsible_org()` fixe l'Organisation responsable d'un Signalement à sa création :
l'Organisation `active`, de type commune ou opérateur, dont la Zone couvre la Position,
la plus précise d'abord (quartier, puis commune d'arrondissement, puis ville) ; à défaut,
l'Organisation plateforme. Elle n'est jamais renvoyée au Citoyen.
"""

from uuid import UUID

from app.core import geo
from app.core.db import current_session, transactional
from app.modules.orgs import repository

# Ligne système insérée par la migration 0003_reports : jamais supprimée, jamais
# étiquetée `is_demo`, sans Zone.
PLATFORM_ORGANIZATION_ID = UUID("00000000-0000-4000-8000-000000000001")


@transactional
def responsible_org(lat: float, lng: float) -> UUID:
    """Identifiant de l'Organisation responsable d'un Signalement à cette Position."""
    zones = geo.zones_covering(current_session(), lat, lng)
    responsible = repository.responsible_by_zone([zone.id for zone in zones])
    for zone in zones:
        if zone.id in responsible:
            return responsible[zone.id]
    return PLATFORM_ORGANIZATION_ID
