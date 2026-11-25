"""Table `zones` : Dakar, ses communes d'arrondissement et ses quartiers (story 1.8).

Propriété de `core/geo`, en lecture seule pour l'API : le DML que les privilèges par
défaut donnent à `teranga_app` (infra/db/initdb/20-roles.sh) est retiré ici.

Données : `migrations/data/zones-dakar.geojson`, construit depuis OpenStreetMap
(© les contributeurs d'OpenStreetMap, ODbL 1.0) par `scripts/build_zones.py` ; source,
date et commande de reconstruction dans `migrations/data/README.md`.

Revision ID: 0002_zones
Revises: 0001_baseline
Create Date: 2026-11-25
"""

import json
from collections.abc import Sequence
from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision: str = "0002_zones"
down_revision: str | Sequence[str] | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "zones-dakar.geojson"
# Rôle de l'API, créé hors Alembic (20-roles.sh).
APP_ROLE = "teranga_app"
# Ordre d'insertion : un parent existe toujours avant ses enfants (clé étrangère).
KIND_ORDER = {"commune": 0, "quartier": 1}

INSERT = sa.text(
    """
    INSERT INTO zones (id, name, kind, parent_id, osm_ref, geog)
    VALUES (
        :id, :name, :kind, :parent_id, :osm_ref,
        ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(:geometry), 4326))::geography
    )
    """
)


def _features() -> list[dict]:
    collection = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    features = collection["features"]
    # La ville (sans parent), puis les communes, puis les quartiers.
    return sorted(
        features,
        key=lambda f: (
            f["properties"]["parent_id"] is not None,
            KIND_ORDER[f["properties"]["kind"]],
        ),
    )


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE zones (
            id text NOT NULL,
            name text NOT NULL,
            kind text NOT NULL,
            parent_id text,
            osm_ref text NOT NULL,
            geog geography(MultiPolygon, 4326) NOT NULL,
            CONSTRAINT pk_zones PRIMARY KEY (id),
            CONSTRAINT fk_zones_parent_id_zones FOREIGN KEY (parent_id) REFERENCES zones (id),
            CONSTRAINT ck_zones_kind CHECK (kind IN ('commune', 'quartier')),
            CONSTRAINT ck_zones_quartier_has_parent
                CHECK (kind <> 'quartier' OR parent_id IS NOT NULL),
            CONSTRAINT ck_zones_id_not_blank CHECK (btrim(id) <> '')
        )
        """
    )
    op.execute("CREATE INDEX ix_zones_geog ON zones USING gist (geog)")
    op.execute("CREATE INDEX ix_zones_parent_id ON zones (parent_id)")

    # op.execute plutôt que la connexion : la migration se rend aussi en SQL (`--sql`).
    for feature in _features():
        props = feature["properties"]
        op.execute(
            INSERT.bindparams(
                id=props["id"],
                name=props["name"],
                kind=props["kind"],
                parent_id=props["parent_id"],
                osm_ref=props["osm_ref"],
                geometry=json.dumps(feature["geometry"], separators=(",", ":")),
            )
        )

    # Une géométrie invalide fausserait ST_Covers : la migration échoue en la nommant.
    op.execute(
        """
        DO $$
        DECLARE invalid text;
        BEGIN
            SELECT string_agg(id, ', ' ORDER BY id) INTO invalid
            FROM zones WHERE NOT ST_IsValid(geog::geometry);
            IF invalid IS NOT NULL THEN
                RAISE EXCEPTION 'Zones invalides : %', invalid;
            END IF;
        END
        $$
        """
    )

    # Lecture seule pour l'API : retirer le DML des privilèges par défaut.
    op.execute(f"REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON zones FROM {APP_ROLE}")
    op.execute(f"GRANT SELECT ON zones TO {APP_ROLE}")


def downgrade() -> None:
    op.execute("DROP TABLE zones")
