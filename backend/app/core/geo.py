"""Zones et règles géographiques (AD-5, story 1.8).

`core/geo` possède la table `zones`, chargée par la migration `0002_zones` depuis
OpenStreetMap et en lecture seule pour l'API. Hiérarchie : Dakar (ville, `commune` sans
parent), ses communes d'arrondissement, puis les quartiers (parent : une commune).

Règles :
  - appartenance : `ST_Covers` sur `geography`, limite incluse ;
  - Zone d'un point : le plus petit quartier qui le couvre, sinon la plus petite commune ;
  - la PWA reçoit la Zone active simplifiée et élargie de 50 m (`load_active_zone`) : elle
    juge de façon tolérante, le serveur tranche exactement.

Aucune coordonnée n'est journalisée ni recopiée dans un message d'erreur. Fonctions
synchrones : session de l'unité de travail en cours (voir `core.db`).
"""

import json
import math
from dataclasses import dataclass
from typing import Any, Literal

from geoalchemy2 import Geography
from pydantic import BaseModel
from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, Table, Text, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import Base
from app.core.enums import ZoneKind

# Marge de la Zone active publiée : la simplification rogne les bords, une Position juste
# à l'intérieur ne doit pas être bloquée par erreur sur l'appareil.
ACTIVE_ZONE_MARGIN_M = 50
# Tolérance de simplification de la Zone publiée, en degrés (~11 m à Dakar) : bien
# inférieure à la marge, le polygone publié couvre toujours la Zone exacte.
ACTIVE_ZONE_SIMPLIFY_DEG = 0.0001
GEOJSON_DECIMALS = 6

# Schéma créé par la migration 0002_zones (seul chemin de schéma) ; déclaré ici pour
# les métadonnées d'Alembic.
zones = Table(
    "zones",
    Base.metadata,
    Column("id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("kind", Text, nullable=False),
    Column("parent_id", Text, ForeignKey("zones.id"), index=True),
    Column("osm_ref", Text, nullable=False),
    Column(
        "geog",
        Geography(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=False),
        nullable=False,
    ),
    CheckConstraint("kind IN ('commune', 'quartier')", name="kind"),
    CheckConstraint("kind <> 'quartier' OR parent_id IS NOT NULL", name="quartier_has_parent"),
    CheckConstraint("btrim(id) <> ''", name="id_not_blank"),
    Index("ix_zones_geog", "geog", postgresql_using="gist"),
)


class InvalidPositionError(ValueError):
    """Latitude ou longitude non finie ou hors bornes (±90, ±180). Le message ne contient
    jamais les valeurs reçues."""

    def __init__(self) -> None:
        super().__init__("Position invalide : latitude ou longitude hors bornes ou non finie")


class UnknownZoneError(LookupError):
    """Aucune Zone ne porte cet identifiant."""


@dataclass(frozen=True)
class Zone:
    id: str
    name: str
    kind: ZoneKind
    parent_id: str | None


class MultiPolygon(BaseModel):
    """Géométrie GeoJSON (RFC 7946) : polygones → anneaux → positions [longitude, latitude]."""

    type: Literal["MultiPolygon"]
    coordinates: list[list[list[list[float]]]]


class ActiveZone(BaseModel):
    """Zone active publiée par `GET /v1/config` : polygone simplifié, élargi de 50 m."""

    id: str
    name: str
    geometry: MultiPolygon


_POINT = "ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography"


def _point_params(lat: float, lng: float) -> dict[str, float]:
    """Paramètres du point ; lève `InvalidPositionError` avant toute requête si la Position
    n'est pas utilisable (NaN, infini, hors bornes)."""
    try:
        lat, lng = float(lat), float(lng)
    except (TypeError, ValueError):
        raise InvalidPositionError from None
    if not (math.isfinite(lat) and math.isfinite(lng) and abs(lat) <= 90 and abs(lng) <= 180):
        raise InvalidPositionError
    return {"lat": lat, "lng": lng}


def in_zone(session: Session, zone_id: str, lat: float, lng: float) -> bool:
    """Vrai si la Zone `zone_id` couvre le point (limite incluse)."""
    params = _point_params(lat, lng)
    covered = session.execute(
        text(f"SELECT ST_Covers(geog, {_POINT}) FROM zones WHERE id = :zone_id"),  # noqa: S608
        {"zone_id": zone_id, **params},
    ).scalar_one_or_none()
    if covered is None:
        raise UnknownZoneError(zone_id)
    return bool(covered)


def in_active_zone(session: Session, lat: float, lng: float) -> bool:
    """Vrai si la Zone active (`ACTIVE_ZONE_ID`) couvre le point (limite incluse)."""
    return in_zone(session, get_settings().active_zone_id, lat, lng)


def zone_of(session: Session, lat: float, lng: float) -> Zone | None:
    """Le plus petit quartier qui couvre le point, sinon la plus petite commune ; None
    hors de toute Zone. Deux quartiers qui se chevauchent : le plus petit l'emporte."""
    params = _point_params(lat, lng)
    row = session.execute(
        text(
            f"""
            SELECT id, name, kind, parent_id FROM zones
            WHERE ST_Covers(geog, {_POINT})
            ORDER BY kind = 'quartier' DESC, ST_Area(geog) ASC, id
            LIMIT 1
            """  # noqa: S608
        ),
        params,
    ).one_or_none()
    if row is None:
        return None
    return Zone(id=row.id, name=row.name, kind=ZoneKind(row.kind), parent_id=row.parent_id)


def zones_covering(session: Session, lat: float, lng: float) -> list[Zone]:
    """Toutes les Zones qui couvrent le point, de la plus précise à la moins précise :
    quartiers, puis communes d'arrondissement, puis la ville (commune sans parent) ; à
    niveau égal, la plus petite d'abord. Liste vide hors de toute Zone."""
    params = _point_params(lat, lng)
    rows = session.execute(
        text(
            f"""
            SELECT id, name, kind, parent_id FROM zones
            WHERE ST_Covers(geog, {_POINT})
            ORDER BY kind = 'quartier' DESC, parent_id IS NULL, ST_Area(geog) ASC, id
            """  # noqa: S608
        ),
        params,
    ).all()
    return [
        Zone(id=row.id, name=row.name, kind=ZoneKind(row.kind), parent_id=row.parent_id)
        for row in rows
    ]


def load_active_zone(session: Session, zone_id: str) -> ActiveZone:
    """Identifiant, nom et GeoJSON de la Zone, simplifiée et élargie de 50 m.

    Lève `UnknownZoneError` si aucune Zone ne porte cet identifiant.
    """
    # Constantes du module écrites dans la requête : aucun paramètre à typer côté SQL.
    row = session.execute(
        text(
            f"""
            SELECT id, name, ST_AsGeoJSON(
                ST_Multi(ST_SimplifyPreserveTopology(
                    ST_Buffer(geog, {float(ACTIVE_ZONE_MARGIN_M)})::geometry,
                    {float(ACTIVE_ZONE_SIMPLIFY_DEG)}
                )),
                {int(GEOJSON_DECIMALS)}
            ) AS geometry
            FROM zones WHERE id = :zone_id
            """  # noqa: S608
        ),
        {"zone_id": zone_id},
    ).one_or_none()
    if row is None:
        raise UnknownZoneError(zone_id)
    geometry: dict[str, Any] = json.loads(row.geometry)
    return ActiveZone(id=row.id, name=row.name, geometry=MultiPolygon.model_validate(geometry))
