// Configuration publique : validation de /v1/config, réseau d'abord puis Dexie (story 1.8).
import 'fake-indexeddb/auto'

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { NetworkError } from '../api/client.ts'
import {
  CONFIG_PATH,
  CONFIG_TIMEOUT_MS,
  fetchPublicConfig,
  InvalidConfigError,
  parsePublicConfig,
  type PublicConfig,
} from '../api/config.ts'
import { db, getMeta, setMeta } from './db.ts'
import { ConfigUnavailableError, loadPublicConfig } from './publicConfig.ts'

const CONFIG: PublicConfig = {
  demo_mode: true,
  env: 'demo',
  model_version: null,
  active_zone: {
    id: 'dakar',
    name: 'Dakar',
    geometry: {
      type: 'MultiPolygon',
      coordinates: [
        [
          [
            [-17.55, 14.65],
            [-17.4, 14.65],
            [-17.4, 14.8],
            [-17.55, 14.8],
            [-17.55, 14.65],
          ],
        ],
      ],
    },
  },
  report_accuracy_flag_m: 50,
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

beforeEach(async () => {
  await db.meta.clear()
})

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('parsePublicConfig', () => {
  it('accepte la réponse de l’API', () => {
    expect(parsePublicConfig(structuredClone(CONFIG))).toEqual(CONFIG)
  })

  it.each([
    ['corps', null],
    ['env', { ...CONFIG, env: 'staging' }],
    ['active_zone', { ...CONFIG, active_zone: undefined }],
    ['active_zone.id', { ...CONFIG, active_zone: { ...CONFIG.active_zone, id: '' } }],
    [
      'active_zone.geometry',
      { ...CONFIG, active_zone: { ...CONFIG.active_zone, geometry: { type: 'Polygon' } } },
    ],
    [
      'active_zone.geometry',
      {
        ...CONFIG,
        active_zone: {
          ...CONFIG.active_zone,
          geometry: { type: 'MultiPolygon', coordinates: [[[[0, 0], [1, 0], [1, 1], [0, 1]]]] },
        },
      },
    ],
    ['report_accuracy_flag_m', { ...CONFIG, report_accuracy_flag_m: 0 }],
    ['report_accuracy_flag_m', { ...CONFIG, report_accuracy_flag_m: '50' }],
  ])('refuse un champ %s invalide', (field, value) => {
    expect(() => parsePublicConfig(value)).toThrow(new InvalidConfigError(field))
  })
})

/** `fetch` qui ne répond jamais : rejette seulement quand la requête est abandonnée. */
function hangingFetch() {
  return vi.fn(
    (request: Request) =>
      new Promise<Response>((_resolve, reject) => {
        const abort = () => reject(new DOMException('abandon', 'AbortError'))
        if (request.signal.aborted) abort()
        request.signal.addEventListener('abort', abort)
      }),
  )
}

describe('fetchPublicConfig', () => {
  it('GET /v1/config par le client généré, réponse validée', async () => {
    const fetchSpy = vi.fn(async (_request: Request) => jsonResponse(CONFIG))
    vi.stubGlobal('fetch', fetchSpy)
    await expect(fetchPublicConfig()).resolves.toEqual(CONFIG)
    expect(fetchSpy).toHaveBeenCalledOnce()
    const [request] = fetchSpy.mock.calls[0]
    expect(request).toBeInstanceOf(Request)
    expect(request.method).toBe('GET')
    expect(new URL(request.url).pathname).toBe(CONFIG_PATH)
    expect(request.cache).toBe('no-store')
    expect(request.headers.get('Accept')).toBe('application/json')
    expect(request.headers.get('X-Device-Id')).toMatch(/^[A-Za-z0-9_-]{43}$/)
    expect(request.signal.aborted).toBe(false)
  })

  it('sans réponse : abandonnée après CONFIG_TIMEOUT_MS (sans AbortSignal.timeout)', async () => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
    const fetchSpy = hangingFetch()
    vi.stubGlobal('fetch', fetchSpy)
    let settled = false
    const result = fetchPublicConfig().finally(() => {
      settled = true
    })
    result.catch(() => undefined)
    // L'Identifiant d'appareil est lu dans Dexie (minuteurs réels) avant l'appel.
    while (fetchSpy.mock.calls.length === 0) await new Promise((resolve) => setImmediate(resolve))
    await vi.advanceTimersByTimeAsync(CONFIG_TIMEOUT_MS - 1)
    expect(settled).toBe(false)
    await vi.advanceTimersByTimeAsync(1)
    await expect(result).rejects.toBeInstanceOf(NetworkError)
  })

  it('statut d’erreur : rejetée (ApiError)', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({ error: {} }, 503)))
    await expect(fetchPublicConfig()).rejects.toMatchObject({ name: 'ApiError', status: 503 })
  })
})

describe('loadPublicConfig : réseau d’abord, puis Dexie', () => {
  it('en ligne : configuration reçue, gardée dans meta.publicConfig', async () => {
    const loaded = await loadPublicConfig(async () => CONFIG)
    expect(loaded).toEqual({ config: CONFIG, source: 'network' })
    expect(await getMeta('publicConfig')).toEqual(CONFIG)
  })

  it('configuration gardée : servie tout de suite, sans attendre le réseau', async () => {
    const older = { ...CONFIG, report_accuracy_flag_m: 99 }
    await setMeta('publicConfig', older)
    let answer: (config: PublicConfig) => void = () => undefined
    const pending = new Promise<PublicConfig>((resolve) => {
      answer = resolve
    })
    const loaded = await loadPublicConfig(() => pending)
    expect(loaded.config).toEqual(older)
    expect(loaded.source).toBe('cache')

    // La lecture en arrière-plan aboutit : Dexie est mis à jour.
    answer(CONFIG)
    await expect(loaded.refreshed).resolves.toEqual(CONFIG)
    expect(await getMeta('publicConfig')).toEqual(CONFIG)
  })

  it('hors ligne : configuration gardée utilisée', async () => {
    await setMeta('publicConfig', CONFIG)
    const loaded = await loadPublicConfig(async () => {
      throw new TypeError('Failed to fetch')
    })
    expect(loaded.config).toEqual(CONFIG)
    expect(loaded.source).toBe('cache')
    await expect(loaded.refreshed).resolves.toBeUndefined()
  })

  it('réponse invalide : configuration gardée utilisée, et non écrasée', async () => {
    await setMeta('publicConfig', CONFIG)
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({ env: 'demo' })))
    const loaded = await loadPublicConfig()
    expect(loaded.source).toBe('cache')
    await loaded.refreshed
    expect(await getMeta('publicConfig')).toEqual(CONFIG)
  })

  it('sans configuration gardée et sans réponse : connexion nécessaire après le délai', async () => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
    const fetchSpy = hangingFetch()
    vi.stubGlobal('fetch', fetchSpy)
    let settled = false
    const result = loadPublicConfig().finally(() => {
      settled = true
    })
    result.catch(() => undefined)
    // Lecture de Dexie d'abord (minuteurs réels) ; vi.waitFor avancerait l'horloge simulée.
    while (fetchSpy.mock.calls.length === 0) await new Promise((resolve) => setImmediate(resolve))
    await vi.advanceTimersByTimeAsync(CONFIG_TIMEOUT_MS - 1)
    expect(settled).toBe(false)
    await vi.advanceTimersByTimeAsync(1)
    await expect(result).rejects.toBeInstanceOf(ConfigUnavailableError)
  })

  it('première fois hors ligne : connexion nécessaire', async () => {
    await expect(
      loadPublicConfig(async () => {
        throw new TypeError('Failed to fetch')
      }),
    ).rejects.toBeInstanceOf(ConfigUnavailableError)
  })

  it('configuration gardée invalide : traitée comme absente', async () => {
    await setMeta('publicConfig', { env: 'demo' })
    await expect(
      loadPublicConfig(async () => {
        throw new TypeError('Failed to fetch')
      }),
    ).rejects.toBeInstanceOf(ConfigUnavailableError)
  })

  it('n’écrit rien dans la console (aucune coordonnée)', async () => {
    const spies = (['log', 'info', 'warn', 'error', 'debug'] as const).map((method) =>
      vi.spyOn(console, method).mockImplementation(() => undefined),
    )
    await loadPublicConfig(async () => CONFIG)
    await loadPublicConfig(async () => {
      throw new TypeError('Failed to fetch')
    })
    for (const spy of spies) expect(spy).not.toHaveBeenCalled()
  })
})
