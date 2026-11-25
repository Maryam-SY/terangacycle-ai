"""Accès à la table `organizations` (propriété de `orgs`, AD-2)."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import bindparam, text

from app.core.db import current_session
from app.core.enums import OrganizationStatus, OrganizationType

# Seuls ces types d'Organisation reçoivent des Signalements par leur Zone (AD-31).
RESPONSIBLE_TYPES = (OrganizationType.COMMUNE, OrganizationType.OPERATOR)

_RESPONSIBLE_BY_ZONE = text(
    """
    SELECT DISTINCT ON (zone_id) zone_id, id FROM organizations
    WHERE status = :status AND type IN :types AND zone_id IN :zone_ids
    ORDER BY zone_id, created_at, id
    """
).bindparams(bindparam("types", expanding=True), bindparam("zone_ids", expanding=True))


def responsible_by_zone(zone_ids: Sequence[str]) -> dict[str, UUID]:
    """Pour chaque Zone donnée qui en a une : l'Organisation `active`, commune ou
    opérateur, qui la couvre (la plus ancienne si plusieurs)."""
    if not zone_ids:
        return {}
    rows = current_session().execute(
        _RESPONSIBLE_BY_ZONE,
        {
            "status": OrganizationStatus.ACTIVE.value,
            "types": [kind.value for kind in RESPONSIBLE_TYPES],
            "zone_ids": list(zone_ids),
        },
    )
    return {row.zone_id: row.id for row in rows}
