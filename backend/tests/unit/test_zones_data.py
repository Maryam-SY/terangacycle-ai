"""Données des Zones (story 1.8) : fichier versionné, script de construction, fumée du bord.

Le fichier `migrations/data/zones-dakar.geojson` est vérifié sans base : licence et
source citées, hiérarchie, identifiants, anneaux fermés, taille. Les fonctions du script
`scripts/build_zones.py` sont vérifiées sur de petites géométries fabriquées.
"""

import importlib
import json
import re
import sys
from pathlib import Path
from types import ModuleType

import pytest

BACKEND = Path(__file__).resolve().parents[2]
DATA = BACKEND / "migrations" / "data"
GEOJSON = DATA / "zones-dakar.geojson"
SCRIPTS = BACKEND / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

build_zones: ModuleType = importlib.import_module("build_zones")
smoke_edge: ModuleType = importlib.import_module("smoke_edge")


@pytest.fixture(scope="module")
def collection() -> dict:
    return json.loads(GEOJSON.read_text(encoding="utf-8"))


# --- Fichier versionné ----------------------------------------------------------------


def test_file_cites_source_and_licence(collection: dict) -> None:
    assert collection["type"] == "FeatureCollection"
    assert collection["attribution"] == "© les contributeurs d'OpenStreetMap"
    assert collection["license"] == "ODbL-1.0"
    assert collection["osm_base"] == "2026-11-25T14:30:28Z"
    assert "12982139" in collection["source"]
    readme = (DATA / "README.md").read_text(encoding="utf-8")
    for expected in (
        "ODbL",
        "contributeurs d'OpenStreetMap",
        "2026-11-25T14:30:28Z",
        "rel(12982139)",
        "build_zones.py",
    ):
        assert expected in readme, expected


def test_file_size_is_bounded() -> None:
    assert GEOJSON.stat().st_size <= 400_000


def test_hierarchy_and_identifiers(collection: dict) -> None:
    props = [feature["properties"] for feature in collection["features"]]
    assert all(set(p) == {"id", "name", "kind", "parent_id", "osm_ref"} for p in props)
    ids = [p["id"] for p in props]
    assert len(ids) == len(set(ids))
    assert all(re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", i) for i in ids)
    by_id = {p["id"]: p for p in props}
    assert by_id["dakar"]["kind"] == "commune" and by_id["dakar"]["parent_id"] is None
    assert by_id["dakar"]["osm_ref"] == "relation/12982139"
    communes = [p for p in props if p["kind"] == "commune" and p["id"] != "dakar"]
    assert len(communes) == 19
    assert {p["parent_id"] for p in communes} == {"dakar"}
    quartiers = [p for p in props if p["kind"] == "quartier"]
    assert quartiers
    assert all(by_id[p["parent_id"]]["kind"] == "commune" for p in quartiers)
    assert {p["kind"] for p in props} == {"commune", "quartier"}


def test_geometries_are_closed_multipolygons_with_6_decimals(collection: dict) -> None:
    for feature in collection["features"]:
        geometry = feature["geometry"]
        assert geometry["type"] == "MultiPolygon", feature["properties"]["id"]
        for polygon in geometry["coordinates"]:
            for ring in polygon:
                assert len(ring) >= 4 and ring[0] == ring[-1]
                for lng, lat in ring:
                    assert -18 < lng < -17 and 14 < lat < 15
                    assert round(lng, 6) == lng and round(lat, 6) == lat


# --- Script de construction -----------------------------------------------------------


def _square(x: float, y: float, size: float) -> list[tuple[float, float]]:
    return [(x, y), (x + size, y), (x + size, y + size), (x, y + size), (x, y)]


@pytest.mark.parametrize(
    ("name", "slug"),
    [
        ("Mermoz-Sacré-Cœur", "mermoz-sacre-coeur"),
        ("Patte d'Oie", "patte-d-oie"),
        ("SCAT URBAM (ILOT M)", "scat-urbam-ilot-m"),
    ],
)
def test_slugify(name: str, slug: str) -> None:
    assert build_zones.slugify(name) == slug


def test_stitch_assembles_ways_in_any_direction() -> None:
    a, b, c, d = (0.0, 0.0), (0.001, 0.0), (0.001, 0.001), (0.0, 0.001)
    rings = build_zones.stitch([[a, b], [c, b], [c, d], [a, d]])
    assert len(rings) == 1
    ring = rings[0]
    assert ring[0] == ring[-1] and set(ring) == {a, b, c, d}


def test_stitch_refuses_an_open_ring() -> None:
    with pytest.raises(build_zones.InvalidGeometry):
        build_zones.stitch([[(0.0, 0.0), (0.001, 0.0)], [(0.001, 0.0), (0.001, 0.001)]])


def test_self_intersecting_ring_is_refused() -> None:
    # Nœud papillon asymétrique : aire non nulle, côtés qui se croisent.
    bowtie = [(0.0, 0.0), (0.002, 0.002), (0.002, 0.0), (0.0, 0.001), (0.0, 0.0)]
    with pytest.raises(build_zones.InvalidGeometry, match="recoupe"):
        build_zones.build_polygons([bowtie], [])


def test_simplify_keeps_ends_and_drops_points_closer_than_tolerance() -> None:
    # Point à ~1 m de la droite : retiré à 3 m ; point à ~55 m : gardé.
    line = [(-17.0, 14.7), (-16.9995, 14.70001), (-16.999, 14.7), (-16.9985, 14.7005)]
    simplified = build_zones.simplify(line, 3.0)
    assert simplified[0] == line[0] and simplified[-1] == line[-1]
    assert (-16.9995, 14.70001) not in simplified
    assert (-16.999, 14.7) in simplified


def test_hole_and_interior_point() -> None:
    outer = _square(-17.5, 14.6, 0.01)
    hole = _square(-17.497, 14.603, 0.004)
    polygons = build_zones.build_polygons([outer], [hole])
    assert len(polygons) == 1 and len(polygons[0]) == 2
    # Extérieur dans le sens trigonométrique, trou dans l'autre (RFC 7946).
    assert build_zones._signed_area(polygons[0][0]) > 0
    assert build_zones._signed_area(polygons[0][1]) < 0
    point = build_zones.interior_point(polygons)
    assert build_zones.point_in_polygons(point, polygons)
    assert not build_zones.point_in_polygons((-17.495, 14.605), polygons)  # dans le trou


def test_build_zones_hierarchy_on_a_fabricated_extract() -> None:
    def way(osm_id: int, ring: list[tuple[float, float]], **tags: str) -> dict:
        geometry = [{"lon": x, "lat": y} for x, y in ring]
        return {"type": "way", "id": osm_id, "tags": tags, "geometry": geometry}

    def relation(osm_id: int, ring: list[tuple[float, float]], **tags: str) -> dict:
        geometry = [{"lon": x, "lat": y} for x, y in ring]
        member = {"type": "way", "ref": osm_id * 10, "role": "outer", "geometry": geometry}
        return {"type": "relation", "id": osm_id, "tags": tags, "members": [member]}

    admin = {"boundary": "administrative"}
    elements = [
        relation(1, _square(-17.5, 14.6, 0.1), name="Ville", admin_level="5", **admin),
        relation(2, _square(-17.5, 14.6, 0.05), name="Commune de Nord", admin_level="8", **admin),
        way(3, _square(-17.49, 14.61, 0.01), name="Quartier A", place="neighbourhood"),
        way(4, _square(-17.49, 14.61, 0.005), name="Quartier A", place="quarter"),
        way(5, _square(-17.43, 14.68, 0.01), name="Hors commune", place="suburb"),
        way(6, _square(-16.9, 14.8, 0.01), name="Thiès", place="suburb"),
        way(7, [(-17.49, 14.61), (-17.48, 14.61)], name="Limite", admin_level="10", **admin),
        way(8, _square(-17.47, 14.62, 0.01), place="neighbourhood"),
    ]
    log: list[str] = []
    zones = build_zones.build_zones(elements, 1, 3.0, log)
    by_id = {zone.id: zone for zone in zones}
    assert [z.id for z in zones][:2] == ["dakar", "nord"]
    assert by_id["nord"].name == "Nord" and by_id["nord"].parent_id == "dakar"
    # Homonymes : tous suffixés par leur référence OSM.
    assert by_id["quartier-a-w3"].parent_id == "nord"
    assert by_id["quartier-a-w4"].parent_id == "nord"
    # Hors des communes mais dans la ville : rattaché à la ville.
    assert by_id["hors-commune"].parent_id == "dakar"
    assert "thies" not in by_id
    assert any("way/6" in line and "hors de" in line for line in log)
    assert any("way/7" in line and "voie ouverte" in line for line in log)
    assert any("way/8" in line and "sans nom" in line for line in log)


def test_a_dropped_commune_stops_the_build() -> None:
    """Une commune invalide n'est jamais écartée en silence : aucun fichier écrit."""
    open_ring = [{"lon": -17.5, "lat": 14.6}, {"lon": -17.45, "lat": 14.6}]
    city_ring = [{"lon": x, "lat": y} for x, y in _square(-17.5, 14.6, 0.1)]

    def relation(osm_id: int, geometry: list[dict], **tags: str) -> dict:
        member = {"type": "way", "ref": osm_id * 10, "role": "outer", "geometry": geometry}
        return {"type": "relation", "id": osm_id, "tags": tags, "members": [member]}

    elements = [
        relation(1, city_ring, name="Ville", admin_level="5", boundary="administrative"),
        relation(2, open_ring, name="Commune de Sud", admin_level="8", boundary="administrative"),
    ]
    with pytest.raises(SystemExit, match="relation/2"):
        build_zones.build_zones(elements, 1, 3.0, [])


# --- Fumée du bord : contrôle de /v1/config -------------------------------------------


def _config(**overrides: object) -> dict:
    ring = [[-17.55, 14.65], [-17.40, 14.65], [-17.40, 14.80], [-17.55, 14.80], [-17.55, 14.65]]
    body = {
        "env": "demo",
        "active_zone": {
            "id": "dakar",
            "name": "Dakar",
            "geometry": {"type": "MultiPolygon", "coordinates": [[ring]]},
        },
        "report_accuracy_flag_m": 50,
    }
    body.update(overrides)
    return body


def test_smoke_edge_accepts_the_published_config(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("ACTIVE_ZONE_ID", "REPORT_ACCURACY_FLAG_M"):
        monkeypatch.setenv(name, smoke_edge.DEFAULTS[name])
    smoke_edge.check_public_config(_config())


@pytest.mark.parametrize(
    "overrides",
    [
        {"active_zone": None},
        {"report_accuracy_flag_m": 30},
        {"active_zone": {"id": "dakar", "name": "Dakar", "geometry": {"type": "Polygon"}}},
        {
            "active_zone": {
                "id": "dakar",
                "name": "Dakar",
                "geometry": {"type": "MultiPolygon", "coordinates": [[[[0, 0], [1, 0], [0, 1]]]]},
            }
        },
    ],
    ids=["sans-zone", "seuil", "pas-multipolygon", "anneau-ouvert"],
)
def test_smoke_edge_refuses_a_wrong_config(
    overrides: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in ("ACTIVE_ZONE_ID", "REPORT_ACCURACY_FLAG_M"):
        monkeypatch.setenv(name, smoke_edge.DEFAULTS[name])
    with pytest.raises(smoke_edge.CheckFailed):
        smoke_edge.check_public_config(_config(**overrides))
