// Appartenance d'un point à la Zone active, jugée sur l'appareil (story 1.8).
// Calcul à plat en degrés (comme une géométrie PostGIS) sur le polygone simplifié et
// élargi de 50 m publié par GET /v1/config : la PWA est tolérante, le serveur tranche
// exactement à la création du Signalement (story 1.11).
import type { MultiPolygon, Position } from '../../api/config.ts'

/** Tolérance de la limite, en degrés (~1 cm) : un point sur un côté est dedans. */
const EPSILON = 1e-7

function onSegment(lng: number, lat: number, [x1, y1]: Position, [x2, y2]: Position): boolean {
  const cross = (x2 - x1) * (lat - y1) - (y2 - y1) * (lng - x1)
  const length = Math.hypot(x2 - x1, y2 - y1)
  if (Math.abs(cross) > EPSILON * Math.max(length, EPSILON)) return false
  return (
    lng >= Math.min(x1, x2) - EPSILON &&
    lng <= Math.max(x1, x2) + EPSILON &&
    lat >= Math.min(y1, y2) - EPSILON &&
    lat <= Math.max(y1, y2) + EPSILON
  )
}

type RingPlace = 'inside' | 'boundary' | 'outside'

function placeInRing(lng: number, lat: number, ring: Position[]): RingPlace {
  let inside = false
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i, i += 1) {
    const a = ring[j]
    const b = ring[i]
    if (onSegment(lng, lat, a, b)) return 'boundary'
    const [xa, ya] = a
    const [xb, yb] = b
    if (ya > lat !== yb > lat && lng < xa + ((lat - ya) * (xb - xa)) / (yb - ya)) {
      inside = !inside
    }
  }
  return inside ? 'inside' : 'outside'
}

/** Vrai si le point est dans le MultiPolygon, limite incluse (limite d'un trou comprise). */
export function multiPolygonCovers(geometry: MultiPolygon, lat: number, lng: number): boolean {
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return false
  return geometry.coordinates.some(([outer, ...holes]) => {
    if (outer === undefined || placeInRing(lng, lat, outer) === 'outside') return false
    return !holes.some((hole) => placeInRing(lng, lat, hole) === 'inside')
  })
}
