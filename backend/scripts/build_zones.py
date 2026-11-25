"""Construit `migrations/data/zones-dakar.geojson` depuis une extraction Overpass (story 1.8).

Données : © les contributeurs d'OpenStreetMap, ODbL 1.0. La requête Overpass, la date
de la base OSM et la commande de reconstruction sont dans `migrations/data/README.md`.

    python backend/scripts/build_zones.py dakar-osm.json \
        -o backend/migrations/data/zones-dakar.geojson

Entrée : sortie Overpass `out geom` (JSON). Sortie : une FeatureCollection GeoJSON dont
chaque Feature est une Zone en MultiPolygon, avec les propriétés `id` (identifiant
lisible et unique), `name`, `kind` (`commune` ou `quartier`), `parent_id` et `osm_ref`.

Hiérarchie :
  - Dakar : la relation de la ville (`--city`, 12982139), `commune` sans parent, `dakar` ;
  - les communes d'arrondissement : relations `admin_level=8`, parent `dakar` ;
  - les quartiers : voies et relations `place=suburb|quarter|neighbourhood`, ou
    `boundary=administrative` de niveau 9 ou 10 ; parent = la plus petite commune qui
    contient leur point intérieur (à défaut, Dakar). Un quartier hors de Dakar est écarté.

Géométrie : chaque voie est simplifiée (Douglas-Peucker, environ 3 m, extrémités gardées,
pour que deux Zones voisines gardent la même limite), puis les anneaux sont assemblés.
Un anneau ouvert, trop court, plat ou qui se recoupe écarte la Zone ; si c'est la
simplification qui le rend invalide, la Zone est reprise sans simplification.
Coordonnées arrondies à 6 décimales (environ 0,1 m), extérieurs dans le sens
trigonométrique (RFC 7946).

Bibliothèque standard seulement. Code de sortie 1 si la ville ou une commune manque, ou
si le fichier dépasse `--max-bytes` (400 Ko par défaut).
"""

import argparse
import json
import math
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

type Point = tuple[float, float]  # (longitude, latitude)
type Ring = list[Point]
type Polygon = list[Ring]  # extérieur puis trous

CITY_RELATION = 12982139
CITY_ID = "dakar"
COMMUNE_LEVEL = "8"
QUARTIER_LEVELS = frozenset({"9", "10"})
QUARTIER_PLACES = frozenset({"suburb", "quarter", "neighbourhood"})
COMMUNE_PREFIX = re.compile(r"^commune (de |d'|du |des )", re.IGNORECASE)
TOLERANCE_M = 3.0
DECIMALS = 6
MAX_BYTES = 400_000
# Projection locale équirectangulaire (Dakar, ~14,7° N), suffisante pour des distances de
# quelques mètres et des comparaisons d'aires.
METERS_PER_DEG_LAT = 110_574.0
METERS_PER_DEG_LON = 111_320.0 * math.cos(math.radians(14.7))

ATTRIBUTION = "© les contributeurs d'OpenStreetMap"
LICENSE = "ODbL-1.0"
LICENSE_URL = "https://opendatacommons.org/licenses/odbl/1-0/"


class InvalidGeometry(ValueError):
    """Géométrie inutilisable : la Zone est écartée."""


@dataclass
class Zone:
    id: str
    name: str
    kind: str
    parent_id: str | None
    osm_ref: str
    polygons: list[Polygon]

    @property
    def area(self) -> float:
        return sum(_ring_area(p[0]) - sum(_ring_area(h) for h in p[1:]) for p in self.polygons)


# --- Géométrie plane ----------------------------------------------------------------


def _xy(point: Point) -> tuple[float, float]:
    return point[0] * METERS_PER_DEG_LON, point[1] * METERS_PER_DEG_LAT


def _signed_area(ring: Ring) -> float:
    """Aire signée en m² (positive dans le sens trigonométrique)."""
    total = 0.0
    for a, b in zip(ring, ring[1:], strict=False):
        (x1, y1), (x2, y2) = _xy(a), _xy(b)
        total += x1 * y2 - x2 * y1
    return total / 2


def _ring_area(ring: Ring) -> float:
    return abs(_signed_area(ring))


def _segment_distance(p: Point, a: Point, b: Point) -> float:
    (px, py), (ax, ay), (bx, by) = _xy(p), _xy(a), _xy(b)
    dx, dy = bx - ax, by - ay
    length2 = dx * dx + dy * dy
    if length2 == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def simplify(line: list[Point], tolerance_m: float) -> list[Point]:
    """Douglas-Peucker ; les deux extrémités sont toujours gardées."""
    if len(line) < 3:
        return list(line)
    keep = [False] * len(line)
    keep[0] = keep[-1] = True
    stack = [(0, len(line) - 1)]
    while stack:
        first, last = stack.pop()
        best, index = 0.0, -1
        for i in range(first + 1, last):
            distance = _segment_distance(line[i], line[first], line[last])
            if distance > best:
                best, index = distance, i
        if index != -1 and best > tolerance_m:
            keep[index] = True
            stack.extend([(first, index), (index, last)])
    return [point for point, kept in zip(line, keep, strict=True) if kept]


def _orientation(a: Point, b: Point, c: Point) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on_segment(a: Point, b: Point, p: Point) -> bool:
    return min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])


def _segments_intersect(a: Point, b: Point, c: Point, d: Point) -> bool:
    o1, o2 = _orientation(a, b, c), _orientation(a, b, d)
    o3, o4 = _orientation(c, d, a), _orientation(c, d, b)
    if ((o1 > 0 > o2) or (o1 < 0 < o2)) and ((o3 > 0 > o4) or (o3 < 0 < o4)):
        return True
    return (
        (o1 == 0 and _on_segment(a, b, c))
        or (o2 == 0 and _on_segment(a, b, d))
        or (o3 == 0 and _on_segment(c, d, a))
        or (o4 == 0 and _on_segment(c, d, b))
    )


def _self_intersects(ring: Ring) -> bool:
    """Vrai si deux côtés non consécutifs de l'anneau se touchent ou se coupent."""
    segments = list(zip(ring, ring[1:], strict=False))
    boxes = [
        (min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1])) for a, b in segments
    ]
    count = len(segments)
    for i in range(count):
        x1, x2, y1, y2 = boxes[i]
        for j in range(i + 2, count):
            if i == 0 and j == count - 1:
                continue  # premier et dernier côtés : consécutifs (anneau fermé)
            u1, u2, v1, v2 = boxes[j]
            if u1 > x2 or u2 < x1 or v1 > y2 or v2 < y1:
                continue
            if _segments_intersect(*segments[i], *segments[j]):
                return True
    return False


def point_in_ring(point: Point, ring: Ring) -> bool:
    """Lancer de rayon (règle pair-impair) ; la limite n'est pas garantie."""
    x, y = point
    inside = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:], strict=False):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def point_in_polygons(point: Point, polygons: list[Polygon]) -> bool:
    return any(
        point_in_ring(point, p[0]) and not any(point_in_ring(point, h) for h in p[1:])
        for p in polygons
    )


def interior_point(polygons: list[Polygon]) -> Point:
    """Point garanti à l'intérieur (comme ST_PointOnSurface) du plus grand polygone.

    Centre de gravité de l'extérieur s'il est dedans ; sinon, milieu du plus large
    segment intérieur sur l'horizontale qui passe par ce centre (ou par le milieu de
    l'emprise)."""
    polygon = max(polygons, key=lambda p: _ring_area(p[0]))
    outer = polygon[0]
    cx = sum(p[0] for p in outer[:-1]) / (len(outer) - 1)
    cy = sum(p[1] for p in outer[:-1]) / (len(outer) - 1)
    if point_in_polygons((cx, cy), [polygon]):
        return cx, cy
    ys = [p[1] for p in outer]
    for y in (cy, (min(ys) + max(ys)) / 2):
        crossings = sorted(
            x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            for ring in polygon
            for (x1, y1), (x2, y2) in zip(ring, ring[1:], strict=False)
            if (y1 > y) != (y2 > y)
        )
        spans = list(zip(crossings[::2], crossings[1::2], strict=False))
        if spans:
            left, right = max(spans, key=lambda span: span[1] - span[0])
            candidate = ((left + right) / 2, y)
            if point_in_polygons(candidate, [polygon]):
                return candidate
    raise InvalidGeometry("aucun point intérieur trouvé")


# --- Anneaux ------------------------------------------------------------------------


def _clean(ring: Ring) -> Ring:
    """Arrondi à 6 décimales, sans point répété consécutif."""
    cleaned: Ring = []
    for lon, lat in ring:
        point = (round(lon, DECIMALS), round(lat, DECIMALS))
        if not cleaned or cleaned[-1] != point:
            cleaned.append(point)
    return cleaned


def _check_ring(ring: Ring) -> None:
    if len(ring) < 4 or ring[0] != ring[-1]:
        raise InvalidGeometry("anneau ouvert ou de moins de 4 points")
    if _ring_area(ring) < 1.0:
        raise InvalidGeometry("anneau plat")
    if _self_intersects(ring):
        raise InvalidGeometry("anneau qui se recoupe")


def stitch(lines: list[list[Point]]) -> list[Ring]:
    """Assemble des voies (extrémités communes) en anneaux fermés."""
    pending = [list(line) for line in lines if len(line) >= 2]
    rings: list[Ring] = []
    while pending:
        current = pending.pop(0)
        while current[0] != current[-1]:
            for index, line in enumerate(pending):
                if line[0] == current[-1]:
                    current = current + line[1:]
                elif line[-1] == current[-1]:
                    current = current + line[-2::-1]
                elif line[-1] == current[0]:
                    current = line[:-1] + current
                elif line[0] == current[0]:
                    current = line[:0:-1] + current
                else:
                    continue
                pending.pop(index)
                break
            else:
                raise InvalidGeometry("anneau impossible à fermer")
        rings.append(current)
    return rings


def _oriented(ring: Ring, counterclockwise: bool) -> Ring:
    return ring if (_signed_area(ring) > 0) == counterclockwise else ring[::-1]


def build_polygons(outers: list[list[Point]], inners: list[list[Point]]) -> list[Polygon]:
    """Polygones valides depuis les voies extérieures et intérieures, déjà simplifiées."""
    outer_rings = [_clean(r) for r in stitch(outers)]
    inner_rings = [_clean(r) for r in stitch(inners)]
    for ring in outer_rings + inner_rings:
        _check_ring(ring)
    polygons: list[Polygon] = [[_oriented(r, True)] for r in outer_rings]
    for hole in inner_rings:
        owners = [p for p in polygons if point_in_ring(hole[0], p[0])]
        if not owners:
            raise InvalidGeometry("trou hors de tout extérieur")
        min(owners, key=lambda p: _ring_area(p[0])).append(_oriented(hole, False))
    return polygons


def _member_lines(element: dict, role: str) -> list[list[Point]]:
    lines = []
    for member in element.get("members", []):
        if member.get("type") != "way":
            continue
        member_role = member.get("role") or "outer"
        if member_role != role:
            continue
        geometry = member.get("geometry")
        if not geometry or any(node is None for node in geometry):
            raise InvalidGeometry("membre sans géométrie")
        lines.append([(node["lon"], node["lat"]) for node in geometry])
    return lines


def element_polygons(element: dict, tolerance_m: float) -> list[Polygon]:
    """Polygones d'une voie fermée ou d'une relation ; simplification abandonnée si elle
    rend la géométrie invalide."""
    if element["type"] == "way":
        line = [(node["lon"], node["lat"]) for node in element.get("geometry") or []]
        if len(line) < 4 or line[0] != line[-1]:
            raise InvalidGeometry("voie ouverte")
        outers, inners = [line], []
    else:
        outers, inners = _member_lines(element, "outer"), _member_lines(element, "inner")
        if not outers:
            raise InvalidGeometry("relation sans extérieur")
    try:
        return build_polygons(
            [simplify(x, tolerance_m) for x in outers], [simplify(x, tolerance_m) for x in inners]
        )
    except InvalidGeometry:
        if tolerance_m == 0:
            raise
        return build_polygons(outers, inners)


# --- Zones --------------------------------------------------------------------------


# Ligatures que la décomposition Unicode ne ramène pas à l'ASCII.
LIGATURES = str.maketrans({"œ": "oe", "Œ": "OE", "æ": "ae", "Æ": "AE"})


def slugify(name: str) -> str:
    """`Mermoz-Sacré-Cœur` → `mermoz-sacre-coeur`."""
    ascii_name = (
        unicodedata.normalize("NFKD", name.translate(LIGATURES)).encode("ascii", "ignore").decode()
    )
    return re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")


def _osm_ref(element: dict) -> str:
    return f"{element['type']}/{element['id']}"


def _is_quartier(tags: dict) -> bool:
    if tags.get("place") in QUARTIER_PLACES:
        return True
    return tags.get("boundary") == "administrative" and tags.get("admin_level") in QUARTIER_LEVELS


def build_zones(
    elements: list[dict], city_relation: int, tolerance_m: float, log: list[str]
) -> list[Zone]:
    city: Zone | None = None
    communes: list[Zone] = []
    candidates: list[tuple[dict, list[Polygon]]] = []

    for element in sorted(elements, key=lambda e: (e["type"], e["id"])):
        tags = element.get("tags") or {}
        is_city = element["type"] == "relation" and element["id"] == city_relation
        is_commune = (
            not is_city
            and element["type"] == "relation"
            and tags.get("boundary") == "administrative"
            and tags.get("admin_level") == COMMUNE_LEVEL
        )
        if not (is_city or is_commune or _is_quartier(tags)):
            continue
        name = (tags.get("name") or "").strip()
        if not name:
            if is_commune:
                raise SystemExit(f"commune {_osm_ref(element)} sans nom")
            log.append(f"écarté {_osm_ref(element)} : sans nom")
            continue
        try:
            polygons = element_polygons(element, tolerance_m)
        except InvalidGeometry as exc:
            if is_commune:
                # Une commune manquante fausserait la hiérarchie : aucun fichier écrit.
                raise SystemExit(f"commune {_osm_ref(element)} ({name}) écartée : {exc}") from None
            log.append(f"écarté {_osm_ref(element)} ({name}) : {exc}")
            continue
        if is_city:
            city = Zone(CITY_ID, name, "commune", None, _osm_ref(element), polygons)
        elif is_commune:
            label = COMMUNE_PREFIX.sub("", name)
            communes.append(
                Zone(slugify(label), label, "commune", CITY_ID, _osm_ref(element), polygons)
            )
        else:
            candidates.append((element, polygons))

    if city is None:
        raise SystemExit(f"relation de la ville {city_relation} absente ou invalide")
    taken = {city.id, *(c.id for c in communes)}
    if len(taken) != len(communes) + 1:
        raise SystemExit("identifiants de communes en double")

    quartiers: list[Zone] = []
    for element, polygons in candidates:
        name = element["tags"]["name"].strip()
        try:
            point = interior_point(polygons)
        except InvalidGeometry as exc:
            log.append(f"écarté {_osm_ref(element)} ({name}) : {exc}")
            continue
        parents = [c for c in communes if point_in_polygons(point, c.polygons)]
        if parents:
            parent = min(parents, key=lambda c: c.area)
        elif point_in_polygons(point, city.polygons):
            parent = city
        else:
            log.append(f"écarté {_osm_ref(element)} ({name}) : hors de {city.name}")
            continue
        quartiers.append(
            Zone(slugify(name), name, "quartier", parent.id, _osm_ref(element), polygons)
        )

    # Identifiant lisible : le nom ; en cas de doublon (entre quartiers, ou avec une
    # commune), tous les homonymes prennent leur référence OSM en suffixe.
    counts: dict[str, int] = {}
    for zone in quartiers:
        counts[zone.id] = counts.get(zone.id, 0) + 1
    for zone in quartiers:
        if counts[zone.id] > 1 or zone.id in taken:
            zone.id = f"{zone.id}-{zone.osm_ref[0]}{zone.osm_ref.split('/')[1]}"
    ids = [z.id for z in quartiers]
    if len(set(ids)) != len(ids) or taken & set(ids):
        raise SystemExit("identifiants de quartiers en double")

    return [city, *sorted(communes, key=lambda z: z.id), *sorted(quartiers, key=lambda z: z.id)]


# --- Sortie -------------------------------------------------------------------------


def _feature(zone: Zone) -> dict:
    return {
        "type": "Feature",
        "properties": {
            "id": zone.id,
            "name": zone.name,
            "kind": zone.kind,
            "parent_id": zone.parent_id,
            "osm_ref": zone.osm_ref,
        },
        "geometry": {
            "type": "MultiPolygon",
            "coordinates": [[[list(point) for point in ring] for ring in p] for p in zone.polygons],
        },
    }


def render(zones: list[Zone], osm_base: str, city_relation: int) -> str:
    """FeatureCollection, une Feature par ligne (diffs lisibles)."""
    header = {
        "type": "FeatureCollection",
        "attribution": ATTRIBUTION,
        "license": LICENSE,
        "license_url": LICENSE_URL,
        "source": f"OpenStreetMap via Overpass API, relation {city_relation} et ses subdivisions",
        "osm_base": osm_base,
    }
    head = json.dumps(header, ensure_ascii=False)[:-1]
    features = ",\n".join(
        json.dumps(_feature(zone), ensure_ascii=False, separators=(",", ":")) for zone in zones
    )
    return f'{head}, "features": [\n{features}\n]}}\n'


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path, help="sortie Overpass `out geom` (JSON)")
    parser.add_argument("-o", "--output", type=Path, required=True, help="GeoJSON produit")
    parser.add_argument("--city", type=int, default=CITY_RELATION, help="relation de la ville")
    parser.add_argument("--tolerance", type=float, default=TOLERANCE_M, help="en mètres")
    parser.add_argument("--max-bytes", type=int, default=MAX_BYTES)
    args = parser.parse_args(argv)

    data = json.loads(args.source.read_text(encoding="utf-8"))
    osm_base = data.get("osm3s", {}).get("timestamp_osm_base", "inconnue")
    log: list[str] = []
    zones = build_zones(data["elements"], args.city, args.tolerance, log)
    text = render(zones, osm_base, args.city)
    size = len(text.encode("utf-8"))

    for line in log:
        print(line, file=sys.stderr)
    kinds = [z.kind for z in zones]
    print(
        f"{kinds.count('commune') - 1} communes, {kinds.count('quartier')} quartiers, "
        f"{len(log)} écartés, {size} octets (base OSM {osm_base})",
        file=sys.stderr,
    )
    if size > args.max_bytes:
        print(f"fichier trop gros : {size} > {args.max_bytes} octets", file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(text.encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
