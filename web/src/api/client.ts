// Client de l'API (story 1.13) : une seule instance `openapi-fetch`, typée par les types
// générés depuis l'OpenAPI (schema.d.ts, `npm run api:types`). Toute requête de la PWA
// passe par `send()` :
// - l'en-tête X-Device-Id (Identifiant d'appareil, Dexie `meta`) est ajouté à chaque
//   requête, et jamais d'en-tête Authorization (Citoyen anonyme) ;
// - une réponse non 2xx devient une `ApiError` (statut, code, clé du message `errors.<code>`
//   de fr.json), une coupure réseau ou un délai dépassé une `NetworkError`.
// Donnée personnelle : l'Identifiant d'appareil n'est jamais écrit dans la console.
import createClient, { type Middleware } from 'openapi-fetch'

import fr from '../i18n/fr.json'
import { ensureDeviceId } from '../offline/device.ts'
import type { components, paths } from './schema'

/** Délai d'une requête, lecture de la réponse comprise. */
export const REQUEST_TIMEOUT_MS = 30_000
export const DEVICE_ID_HEADER = 'X-Device-Id'

export type ErrorCode = components['schemas']['ErrorCode']
/** Clé d'un message d'erreur de fr.json. */
export type ErrorMessageKey = `errors.${keyof typeof fr.errors}`

const FALLBACK_CODE = 'internal_error'

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function isKnownCode(code: string): code is keyof typeof fr.errors {
  return Object.hasOwn(fr.errors, code)
}

/** Réponse non 2xx de l'API. */
export class ApiError extends Error {
  readonly status: number
  /** Code de l'enveloppe d'erreur ; `internal_error` si l'enveloppe manque. */
  readonly code: string
  /** `errors.<code>` si fr.json connaît le code, sinon `errors.internal_error`. */
  readonly messageKey: ErrorMessageKey
  /** Faux si la réponse n'avait pas d'enveloppe d'erreur lisible (page d'erreur du proxy). */
  readonly enveloped: boolean

  constructor(status: number, code: string | undefined) {
    super(`réponse ${status}${code ? ` (${code})` : ''}`)
    this.name = 'ApiError'
    this.status = status
    this.enveloped = code !== undefined
    this.code = code ?? FALLBACK_CODE
    this.messageKey = `errors.${isKnownCode(this.code) ? this.code : FALLBACK_CODE}`
  }

  /** 5xx, ou réponse sans enveloppe (un 502 de Caddy, par exemple) : erreur passagère côté
   *  serveur, la même requête peut être renvoyée. */
  get isServerError(): boolean {
    return this.status >= 500 || !this.enveloped
  }
}

/** Aucune réponse : coupure réseau, délai dépassé, ou requête impossible à préparer. */
export class NetworkError extends Error {
  constructor(options?: { cause?: unknown }) {
    super('requête sans réponse', options)
    this.name = 'NetworkError'
  }
}

/** Code de l'enveloppe `{ error: { code } }`, ou `undefined` si elle manque. */
function envelopeCode(body: unknown): string | undefined {
  if (!isRecord(body) || !isRecord(body.error)) return undefined
  const { code } = body.error
  return typeof code === 'string' && code !== '' ? code : undefined
}

/** `ApiError` d'une réponse d'erreur, à partir de son corps (déjà lu). */
export function toApiError(status: number, body: unknown): ApiError {
  return new ApiError(status, envelopeCode(body))
}

const deviceIdMiddleware: Middleware = {
  async onRequest({ request }) {
    request.headers.set(DEVICE_ID_HEADER, await ensureDeviceId())
    request.headers.delete('Authorization')
    return request
  },
}

// Sous Node (tests Vitest), `location` n'existe pas et `Request` refuse une adresse
// relative : origine fictive. Dans le navigateur, l'origine de la PWA (même origine que
// l'API, derrière Caddy).
const BASE_URL = typeof location === 'undefined' ? 'http://localhost' : location.origin

/** Instance unique. `fetch` est relu à chaque requête : les tests le remplacent après
 *  l'import. */
export const client = createClient<paths>({
  baseUrl: BASE_URL,
  fetch: (request) => globalThis.fetch(request),
})
client.use(deviceIdMiddleware)

interface ClientResult<T> {
  data?: T
  error?: unknown
  response: Response
}

export interface Sent<T> {
  data: T
  status: number
}

/** Lance une requête du client avec un délai (AbortController et setTimeout plutôt
 *  qu'AbortSignal.timeout, absent des navigateurs anciens), puis traduit l'échec :
 *  `NetworkError` sans réponse, `ApiError` pour un statut non 2xx. */
export async function send<T>(
  call: (signal: AbortSignal) => Promise<ClientResult<T>>,
  timeoutMs: number = REQUEST_TIMEOUT_MS,
): Promise<Sent<T>> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  let result: ClientResult<T>
  try {
    result = await call(controller.signal)
  } catch (cause) {
    throw new NetworkError({ cause })
  } finally {
    clearTimeout(timer)
  }
  const { response } = result
  if (!response.ok) throw toApiError(response.status, result.error)
  return { data: result.data as T, status: response.status }
}
