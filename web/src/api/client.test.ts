// Client API (story 1.13) : X-Device-Id sur chaque requête, jamais Authorization ; erreurs
// traduites en ApiError (code, message de fr.json) ou NetworkError (coupure, délai).
import 'fake-indexeddb/auto'

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import fr from '../i18n/fr.json'
import { db } from '../offline/db.ts'
import { DEVICE_ID_PATTERN, ensureDeviceId } from '../offline/device.ts'
import {
  ApiError,
  client,
  DEVICE_ID_HEADER,
  NetworkError,
  REQUEST_TIMEOUT_MS,
  send,
  toApiError,
} from './client.ts'
import openapi from './openapi.json'

function envelope(code: string, status: number): Response {
  return new Response(JSON.stringify({ error: { code, message: 'serveur', request_id: 'r' } }), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function getConfig() {
  return send((signal) => client.GET('/v1/config', { signal }))
}

async function rejection(promise: Promise<unknown>): Promise<unknown> {
  try {
    await promise
  } catch (error) {
    return error
  }
  throw new Error('promesse résolue, rejet attendu')
}

beforeEach(async () => {
  await db.meta.clear()
})

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('en-têtes', () => {
  it('X-Device-Id (Identifiant de Dexie `meta`) sur chaque requête, jamais Authorization', async () => {
    const fetchSpy = vi.fn(async (_request: Request) => Response.json({}))
    vi.stubGlobal('fetch', fetchSpy)
    await getConfig()
    await send((signal) =>
      client.GET('/v1/config', { signal, headers: { Authorization: 'Bearer jeton' } }),
    )
    const deviceId = await ensureDeviceId()
    expect(deviceId).toMatch(DEVICE_ID_PATTERN)
    expect(fetchSpy).toHaveBeenCalledTimes(2)
    for (const [request] of fetchSpy.mock.calls) {
      expect(request).toBeInstanceOf(Request)
      expect(request.headers.get(DEVICE_ID_HEADER)).toBe(deviceId)
      expect(request.headers.has('Authorization')).toBe(false)
      expect(new URL(request.url).pathname).toBe('/v1/config')
    }
  })

  it('n’écrit rien dans la console (ni Identifiant d’appareil)', async () => {
    const spies = (['log', 'info', 'warn', 'error', 'debug'] as const).map((method) =>
      vi.spyOn(console, method).mockImplementation(() => undefined),
    )
    vi.stubGlobal('fetch', vi.fn(async () => envelope('internal_error', 500)))
    await rejection(getConfig())
    for (const spy of spies) expect(spy).not.toHaveBeenCalled()
  })
})

describe('réponses', () => {
  it('2xx : données lues et statut', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => Response.json({ env: 'demo' })))
    await expect(getConfig()).resolves.toEqual({ data: { env: 'demo' }, status: 200 })
  })

  it.each([
    [422, 'outside_active_zone'],
    [422, 'consent_required'],
    [409, 'client_uuid_conflict'],
    [413, 'photo_too_large'],
    [400, 'invalid_device_id'],
  ])('%i %s : ApiError avec le message errors.<code>', async (status, code) => {
    vi.stubGlobal('fetch', vi.fn(async () => envelope(code, status)))
    const error = await rejection(getConfig())
    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status, code, messageKey: `errors.${code}`, enveloped: true })
    expect((error as ApiError).isServerError).toBe(false)
  })

  it('code inconnu de fr.json : message errors.internal_error, code gardé', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => envelope('rate_limited', 429)))
    const error = await rejection(getConfig())
    expect(error).toMatchObject({ status: 429, code: 'rate_limited', messageKey: 'errors.internal_error' })
  })

  it('503 avec enveloppe : erreur serveur, son message', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => envelope('storage_unavailable', 503)))
    const error = (await rejection(getConfig())) as ApiError
    expect(error.messageKey).toBe('errors.storage_unavailable')
    expect(error.isServerError).toBe(true)
  })

  it.each([
    ['502 de Caddy (HTML)', new Response('<html>502 Bad Gateway</html>', { status: 502 })],
    ['corps vide', new Response(null, { status: 500 })],
    ['JSON sans enveloppe', Response.json({ detail: 'x' }, { status: 504 })],
    ['404 sans enveloppe (proxy)', new Response('introuvable', { status: 404 })],
  ])('enveloppe absente ou illisible (%s) : erreur 5xx, errors.internal_error', async (_, response) => {
    vi.stubGlobal('fetch', vi.fn(async () => response))
    const error = (await rejection(getConfig())) as ApiError
    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ code: 'internal_error', messageKey: 'errors.internal_error', enveloped: false })
    expect(error.isServerError).toBe(true)
  })

  it('toApiError lit l’enveloppe d’un corps déjà lu', () => {
    expect(toApiError(422, { error: { code: 'validation_error' } })).toMatchObject({
      code: 'validation_error',
      messageKey: 'errors.validation_error',
    })
    expect(toApiError(422, 'texte').enveloped).toBe(false)
    expect(toApiError(422, { error: { code: 42 } }).enveloped).toBe(false)
  })
})

describe('sans réponse', () => {
  it('coupure réseau : NetworkError, avec la cause', async () => {
    const cause = new TypeError('Failed to fetch')
    vi.stubGlobal('fetch', vi.fn(async () => Promise.reject(cause)))
    const error = await rejection(getConfig())
    expect(error).toBeInstanceOf(NetworkError)
    expect((error as NetworkError).cause).toBe(cause)
  })

  it('délai de 30 s dépassé : requête abandonnée, NetworkError', async () => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
    const fetchSpy = vi.fn(
      (request: Request) =>
        new Promise<Response>((_resolve, reject) => {
          const abort = () => reject(new DOMException('abandon', 'AbortError'))
          if (request.signal.aborted) abort()
          request.signal.addEventListener('abort', abort)
        }),
    )
    vi.stubGlobal('fetch', fetchSpy)
    let settled = false
    const result = getConfig().finally(() => {
      settled = true
    })
    result.catch(() => undefined)
    // L'Identifiant d'appareil est lu dans Dexie (minuteurs réels) avant l'appel.
    while (fetchSpy.mock.calls.length === 0) await new Promise((resolve) => setImmediate(resolve))
    await vi.advanceTimersByTimeAsync(REQUEST_TIMEOUT_MS - 1)
    expect(settled).toBe(false)
    await vi.advanceTimersByTimeAsync(1)
    await expect(result).rejects.toBeInstanceOf(NetworkError)
  })

  it('réponse 2xx illisible : NetworkError (rien d’exploitable)', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response('{pas du json', { headers: { 'Content-Type': 'application/json' } })),
    )
    await expect(getConfig()).rejects.toBeInstanceOf(NetworkError)
  })
})

describe('catalogue des messages', () => {
  it('chaque code de l’OpenAPI a son message errors.<code> dans fr.json', () => {
    const codes = openapi.components.schemas.ErrorCode.enum
    expect(codes.length).toBeGreaterThan(0)
    expect(codes.filter((code) => !Object.hasOwn(fr.errors, code))).toEqual([])
  })
})
