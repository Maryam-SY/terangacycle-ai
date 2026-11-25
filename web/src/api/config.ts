// Lecteur de GET /v1/config (configuration publique de l'instance, AD-14).
// Petit client écrit à la main en attendant le client généré depuis l'OpenAPI
// (story 1.13) : la réponse est validée champ par champ avant tout usage.

/** Position GeoJSON : [longitude, latitude]. */
export type Position = [number, number]

/** MultiPolygon GeoJSON (RFC 7946) : polygones → anneaux (extérieur puis trous). */
export interface MultiPolygon {
  type: 'MultiPolygon'
  coordinates: Position[][][]
}

export interface ActiveZone {
  id: string
  name: string
  /** Polygone simplifié et élargi de 50 m par le serveur. */
  geometry: MultiPolygon
}

export interface PublicConfig {
  demo_mode: boolean
  env: 'dev' | 'demo' | 'prod'
  model_version: string | null
  active_zone: ActiveZone
  /** Au-delà de cette précision (mètres), la PWA invite à patienter. */
  report_accuracy_flag_m: number
}

export const CONFIG_PATH = '/v1/config'
/** Délai de la requête : au-delà, la configuration gardée sur l'appareil prend le relais. */
export const CONFIG_TIMEOUT_MS = 8000

export class InvalidConfigError extends Error {
  constructor(field: string) {
    super(`configuration publique invalide : ${field}`)
    this.name = 'InvalidConfigError'
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function isPosition(value: unknown): value is Position {
  if (!Array.isArray(value) || value.length < 2) return false
  const [lng, lat] = value as unknown[]
  return (
    typeof lng === 'number' &&
    typeof lat === 'number' &&
    Number.isFinite(lng) &&
    Number.isFinite(lat) &&
    Math.abs(lng) <= 180 &&
    Math.abs(lat) <= 90
  )
}

function isRing(value: unknown): boolean {
  if (!Array.isArray(value) || value.length < 4 || !value.every(isPosition)) return false
  const first = value[0] as Position
  const last = value[value.length - 1] as Position
  return first[0] === last[0] && first[1] === last[1]
}

function isMultiPolygon(value: unknown): value is MultiPolygon {
  if (!isRecord(value) || value.type !== 'MultiPolygon') return false
  const { coordinates } = value
  return (
    Array.isArray(coordinates) &&
    coordinates.length > 0 &&
    coordinates.every(
      (polygon) => Array.isArray(polygon) && polygon.length > 0 && polygon.every(isRing),
    )
  )
}

/** Configuration validée ; lève `InvalidConfigError` en nommant le premier champ fautif. */
export function parsePublicConfig(value: unknown): PublicConfig {
  if (!isRecord(value)) throw new InvalidConfigError('corps')
  const { demo_mode, env, model_version, active_zone, report_accuracy_flag_m } = value
  if (typeof demo_mode !== 'boolean') throw new InvalidConfigError('demo_mode')
  if (env !== 'dev' && env !== 'demo' && env !== 'prod') throw new InvalidConfigError('env')
  if (model_version !== null && typeof model_version !== 'string') {
    throw new InvalidConfigError('model_version')
  }
  if (!isRecord(active_zone)) throw new InvalidConfigError('active_zone')
  const { id, name, geometry } = active_zone
  if (typeof id !== 'string' || id === '') throw new InvalidConfigError('active_zone.id')
  if (typeof name !== 'string' || name === '') throw new InvalidConfigError('active_zone.name')
  if (!isMultiPolygon(geometry)) throw new InvalidConfigError('active_zone.geometry')
  if (
    typeof report_accuracy_flag_m !== 'number' ||
    !Number.isInteger(report_accuracy_flag_m) ||
    report_accuracy_flag_m < 1
  ) {
    throw new InvalidConfigError('report_accuracy_flag_m')
  }
  return {
    demo_mode,
    env,
    model_version,
    active_zone: { id, name, geometry },
    report_accuracy_flag_m,
  }
}

/** GET /v1/config, validée. Lève une erreur (réseau, statut, délai, contenu) sans
 *  autre détail : l'appelant se replie sur la configuration gardée. */
export async function fetchPublicConfig(timeoutMs = CONFIG_TIMEOUT_MS): Promise<PublicConfig> {
  // AbortController et setTimeout plutôt que AbortSignal.timeout, absent des navigateurs
  // plus anciens (Android 8). Le minuteur est arrêté dès que la lecture se termine.
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const response = await fetch(CONFIG_PATH, {
      headers: { Accept: 'application/json' },
      cache: 'no-store',
      signal: controller.signal,
    })
    if (!response.ok) throw new Error(`GET ${CONFIG_PATH} : statut ${response.status}`)
    return parsePublicConfig(await response.json())
  } finally {
    clearTimeout(timer)
  }
}
