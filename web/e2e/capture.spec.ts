// Story 1.8 : vérifier la Position et la Zone active avant la photo (écran 2 · Capture).
// Une ligne de la matrice I/O de la spec par test, en 390×844 sur la PWA construite.
// Géolocalisation simulée (pilotée par le test), GET /v1/config intercepté (Zone de
// test, pas les données OSM), audit axe à chaque état et aucune coordonnée en console.
import { readFileSync } from 'node:fs'

import AxeBuilder from '@axe-core/playwright'
import { test as base, expect, type Page, type Route } from '@playwright/test'

declare global {
  interface Window {
    __geo?: {
      calls: string[]
      /** Options passées à chaque `watchPosition`. */
      options: (PositionOptions | undefined)[]
      watchers: () => number
      emit: (lat: number, lng: number, accuracy: number) => void
      fail: (code: number) => void
    }
    __cameraCalls?: number
  }
}

interface Texts {
  consent: { accept: string }
  capture: {
    title: string
    position: {
      locating: string
      detected: string
      wait: string
      continue: string
      denied: string
      unavailable: string
    }
    zone: { outside: string; firstConnection: string }
    retry: string
    trigger: string
    rule: { title: string }
    photo: { unreadable: string }
    preview: { alt: string; continue: string; retake: string }
  }
  details: { title: string }
}

const fr = JSON.parse(
  readFileSync(new URL('../src/i18n/fr.json', import.meta.url), 'utf8'),
) as Texts

const CAPTURE_URL = /\/signaler\/capture$/
// Photo de test (PNG 8×6 rouge) : décodée et ré-encodée en JPEG par la PWA.
const PHOTO = {
  name: 'depot.png',
  mimeType: 'image/png',
  buffer: Buffer.from(
    'iVBORw0KGgoAAAANSUhEUgAAAAgAAAAGCAIAAABxZ0isAAAAFElEQVR4nGM8oaHBgA0wYRWlkwQAppoBJCiW4EgAAAAASUVORK5CYII=',
    'base64',
  ),
}
const PERMISSION_DENIED = 1
const POSITION_UNAVAILABLE = 2

// Zone de test : un rectangle autour de Dakar (sommet sud-ouest : SW).
const SW = { lat: 14.65, lng: -17.55 }
const ZONE_RING = [
  [SW.lng, SW.lat],
  [-17.4, 14.65],
  [-17.4, 14.8],
  [-17.55, 14.8],
  [SW.lng, SW.lat],
]
const CONFIG = {
  demo_mode: true,
  env: 'demo',
  model_version: null,
  active_zone: {
    id: 'dakar',
    name: 'Dakar',
    geometry: { type: 'MultiPolygon', coordinates: [[ZONE_RING]] },
  },
  report_accuracy_flag_m: 50,
}
// Points témoins ; leurs coordonnées ne doivent jamais apparaître dans la console.
const PLATEAU = { lat: 14.6708, lng: -17.4381 }
const THIES = { lat: 14.791, lng: -16.9359 }
// Origine de la PWA servie par `vite preview` (playwright.config.ts).
const APP_ORIGIN = 'http://127.0.0.1:4173'
const COORDINATE_TEXTS = ['14.67', '17.43', '14.79', '16.93', '14.65', '17.55']

interface Capture {
  /** Messages de console de la page. */
  consoleMessages: string[]
  /** Réponse de GET /v1/config : la configuration, ou un échec réseau. */
  setNetwork: (mode: 'online' | 'offline') => void
  /** Nombre de requêtes GET /v1/config reçues. */
  configRequests: () => number
}

const test = base.extend<{ capture: Capture }>({
  // Fixture automatique : chaque test a la géolocalisation simulée et /v1/config intercepté.
  // Second argument nommé `provide` (et non `use`) : la règle rules-of-hooks le prendrait pour un hook.
  capture: [
    async ({ page }, provide) => {
      await page.addInitScript(() => {
        type Watcher = { success: PositionCallback; error?: PositionErrorCallback | null }
        const watchers = new Map<number, Watcher>()
        const calls: string[] = []
        const options: (PositionOptions | undefined)[] = []
        let nextId = 1
        const geolocation = {
          watchPosition(
            success: PositionCallback,
            error?: PositionErrorCallback | null,
            given?: PositionOptions,
          ) {
            calls.push('watchPosition')
            options.push(given ? { ...given } : undefined)
            const id = nextId
            nextId += 1
            watchers.set(id, { success, error })
            return id
          },
          clearWatch(id: number) {
            calls.push('clearWatch')
            watchers.delete(id)
          },
          getCurrentPosition() {
            calls.push('getCurrentPosition')
          },
        }
        Object.defineProperty(navigator, 'geolocation', { configurable: true, get: () => geolocation })
        Object.defineProperty(window, '__geo', {
          value: {
            calls,
            options,
            watchers: () => watchers.size,
            emit(lat: number, lng: number, accuracy: number) {
              const position = {
                coords: {
                  latitude: lat,
                  longitude: lng,
                  accuracy,
                  altitude: null,
                  altitudeAccuracy: null,
                  heading: null,
                  speed: null,
                },
                timestamp: Date.now(),
              } as unknown as GeolocationPosition
              for (const watcher of watchers.values()) watcher.success(position)
            },
            fail(code: number) {
              const error = {
                code,
                message: 'simulé',
                PERMISSION_DENIED: 1,
                POSITION_UNAVAILABLE: 2,
                TIMEOUT: 3,
              } as unknown as GeolocationPositionError
              for (const watcher of watchers.values()) watcher.error?.(error)
            },
          },
        })
        // Appareil photo : jamais demandé dans cette story (story 1.9).
        let cameraCalls = 0
        Object.defineProperty(window, '__cameraCalls', { get: () => cameraCalls })
        if (navigator.mediaDevices) {
          Object.defineProperty(navigator.mediaDevices, 'getUserMedia', {
            configurable: true,
            value: () => {
              cameraCalls += 1
              return Promise.reject(new DOMException('espion', 'NotAllowedError'))
            },
          })
        }
      })

      let mode: 'online' | 'offline' = 'online'
      let requests = 0
      await page.route('**/v1/config', async (route: Route) => {
        requests += 1
        if (mode === 'offline') await route.abort('internetdisconnected')
        else await route.fulfill({ json: CONFIG })
      })
      const consoleMessages: string[] = []
      page.on('console', (message) => consoleMessages.push(message.text()))
      // Toutes les requêtes du contexte (page et workers), avec leur corps.
      const outgoing: { method: string; url: string; body: string }[] = []
      page.context().on('request', (request) =>
        outgoing.push({
          method: request.method(),
          url: request.url(),
          body: request.postData() ?? '',
        }),
      )

      await provide({
        consoleMessages,
        setNetwork: (value) => {
          mode = value
        },
        configRequests: () => requests,
      })

      // Aucune coordonnée dans la console, quel que soit le test.
      const leaked = consoleMessages.filter((text) =>
        COORDINATE_TEXTS.some((coordinate) => text.includes(coordinate)),
      )
      expect(leaked).toEqual([])

      // Rien d'autre ne quitte la page que la coquille (même origine, GET) et
      // GET /v1/config : ni Position envoyée, ni autre route de l'API, ni autre site.
      const unexpected = outgoing.filter(({ method, url }) => {
        const target = new URL(url)
        if (target.protocol === 'data:' || target.protocol === 'blob:') return false
        if (target.origin !== APP_ORIGIN || method !== 'GET') return true
        return target.pathname.startsWith('/v1/') && target.pathname !== '/v1/config'
      })
      expect(unexpected).toEqual([])
      const withCoordinates = outgoing.filter(({ url, body }) =>
        COORDINATE_TEXTS.some((coordinate) => url.includes(coordinate) || body.includes(coordinate)),
      )
      expect(withCoordinates).toEqual([])
    },
    { auto: true },
  ],
})

/** Consentement accepté par l'interface, puis écran 2 ; le suivi de la Position démarre. */
async function openCapture(page: Page) {
  await page.goto('/signaler')
  await page.getByRole('button', { name: fr.consent.accept }).click()
  await expect(page).toHaveURL(CAPTURE_URL)
  await expect(page.getByRole('heading', { level: 1, name: fr.capture.title })).toBeVisible()
  await expectWatching(page)
}

async function expectWatching(page: Page) {
  await expect.poll(() => page.evaluate(() => window.__geo?.watchers() ?? 0)).toBe(1)
}

function emit(page: Page, point: { lat: number; lng: number }, accuracy: number) {
  return page.evaluate(
    ({ lat, lng, accuracy }) => window.__geo?.emit(lat, lng, accuracy),
    { ...point, accuracy },
  )
}

function fail(page: Page, code: number) {
  return page.evaluate((value) => window.__geo?.fail(value), code)
}

function trigger(page: Page) {
  return page.getByRole('button', { name: fr.capture.trigger })
}

function detected(accuracy: number): string {
  return fr.capture.position.detected.replace('{{accuracy}}', String(accuracy))
}

async function expectNoSeriousViolations(page: Page) {
  const { violations } = await new AxeBuilder({ page }).analyze()
  const serious = violations
    .filter((violation) => violation.impact === 'critical' || violation.impact === 'serious')
    .map((violation) => `${violation.id} (${violation.impact}) : ${violation.help}`)
  expect(serious).toEqual([])
}

test('position bonne (± 12 m) : « Position détectée, précision ± 12 m », déclencheur actif', async ({
  page,
}) => {
  await openCapture(page)
  await expect(page.getByText(fr.capture.position.locating)).toBeVisible()
  await expect(trigger(page)).toBeDisabled()

  await emit(page, PLATEAU, 12)
  await expect(page.getByText(detected(12))).toBeVisible()
  await expect(page.getByText(fr.capture.position.wait)).toHaveCount(0)
  await expect(trigger(page)).toBeEnabled()

  // Haute précision demandée, aucune position en cache.
  const options = await page.evaluate(() => window.__geo?.options ?? [])
  expect(options).toHaveLength(1)
  expect(options[0]?.enableHighAccuracy).toBe(true)
  expect(options[0]?.maximumAge).toBe(0)

  const box = await trigger(page).boundingBox()
  expect(box?.height).toBeGreaterThanOrEqual(44)
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  )
  expect(overflow).toBeLessThanOrEqual(0)
  await expectNoSeriousViolations(page)

  // Story 1.9 : consigne visible, prise de vue directe par le sélecteur de fichier (pas de
  // flux getUserMedia), aperçu, puis « Continuer » vers l'écran 3.
  await expect(page.getByRole('heading', { name: fr.capture.rule.title })).toBeVisible()
  await expect(page.getByTestId('camera-input')).toHaveAttribute('capture', 'environment')
  const chooser = page.waitForEvent('filechooser')
  await trigger(page).click()
  await (await chooser).setFiles(PHOTO)
  await expect(page.getByRole('img', { name: fr.capture.preview.alt })).toBeVisible()
  expect(await page.evaluate(() => window.__cameraCalls)).toBe(0)

  // « Reprendre la photo » ramène la consigne ; « Continuer » ouvre l'écran 3.
  await page.getByRole('button', { name: fr.capture.preview.retake }).click()
  await expect(page.getByRole('heading', { name: fr.capture.rule.title })).toBeVisible()
  const again = page.waitForEvent('filechooser')
  await trigger(page).click()
  await (await again).setFiles(PHOTO)
  await page.getByRole('button', { name: fr.capture.preview.continue }).click()
  await expect(page).toHaveURL(/\/signaler\/details$/)
  await expect(page.getByRole('heading', { name: fr.details.title })).toBeVisible()
})

test('photo illisible : message, rien n’est gardé, la consigne reste', async ({ page }) => {
  await openCapture(page)
  await emit(page, PLATEAU, 12)
  const chooser = page.waitForEvent('filechooser')
  await trigger(page).click()
  await (await chooser).setFiles({
    name: 'photo.heic',
    mimeType: 'image/heic',
    buffer: Buffer.from('pas une image lisible'),
  })
  await expect(page.getByText(fr.capture.photo.unreadable)).toBeVisible()
  await expect(page.getByRole('img', { name: fr.capture.preview.alt })).toHaveCount(0)
  await expect(page.getByRole('heading', { name: fr.capture.rule.title })).toBeVisible()
})

test('imprécise (± 80 m) : invitation ambre, « Continuer quand même », puis déclencheur actif', async ({
  page,
}) => {
  await openCapture(page)
  await emit(page, PLATEAU, 80)
  await expect(page.getByText(detected(80))).toBeVisible()
  const invitation = page.getByText(fr.capture.position.wait)
  await expect(invitation).toBeVisible()
  await expect(trigger(page)).toBeDisabled()
  await expectNoSeriousViolations(page)

  await page.getByRole('button', { name: fr.capture.position.continue }).click()
  await expect(trigger(page)).toBeEnabled()
  await expect(invitation).toHaveCount(0)
})

test('imprécise puis précision ≤ 50 m : déclencheur actif sans « Continuer »', async ({ page }) => {
  await openCapture(page)
  await emit(page, PLATEAU, 80)
  await expect(trigger(page)).toBeDisabled()

  await emit(page, PLATEAU, 30)
  await expect(page.getByText(detected(30))).toBeVisible()
  await expect(page.getByText(fr.capture.position.wait)).toHaveCount(0)
  await expect(trigger(page)).toBeEnabled()
  await expectNoSeriousViolations(page)
})

test('exactement 50 m : pas d’invitation', async ({ page }) => {
  await openCapture(page)
  await emit(page, PLATEAU, 50)
  await expect(page.getByText(detected(50))).toBeVisible()
  await expect(page.getByText(fr.capture.position.wait)).toHaveCount(0)
  await expect(page.getByRole('button', { name: fr.capture.position.continue })).toHaveCount(0)
  await expect(trigger(page)).toBeEnabled()
  await expectNoSeriousViolations(page)
})

test('hors Zone (Thiès) : « TerangaCycle n’est pas encore actif ici », déclencheur inactif', async ({
  page,
}) => {
  await openCapture(page)
  await emit(page, THIES, 10)
  await expect(page.getByText(fr.capture.zone.outside)).toBeVisible()
  await expect(trigger(page)).toBeDisabled()
  // La raison est annoncée avec le déclencheur.
  await expect(trigger(page)).toHaveAccessibleDescription(fr.capture.zone.outside)
  await expectNoSeriousViolations(page)
})

test('limite : un sommet de la Zone publiée est dans la Zone', async ({ page }) => {
  await openCapture(page)
  await emit(page, SW, 10)
  await expect(page.getByText(detected(10))).toBeVisible()
  await expect(trigger(page)).toBeEnabled()
  await expectNoSeriousViolations(page)
})

test('refus de la permission : explication sans culpabiliser, « Réessayer » relance le suivi', async ({
  page,
}) => {
  await openCapture(page)
  await fail(page, PERMISSION_DENIED)
  await expect(page.getByText(fr.capture.position.denied)).toBeVisible()
  await expect(trigger(page)).toBeDisabled()
  await expectNoSeriousViolations(page)

  await page.getByRole('button', { name: fr.capture.retry }).click()
  await expect(page.getByText(fr.capture.position.locating)).toBeVisible()
  await expectWatching(page)
  const calls = await page.evaluate(() => [...(window.__geo?.calls ?? [])])
  expect(calls.filter((call) => call === 'watchPosition')).toHaveLength(2)
  expect(calls).toContain('clearWatch')

  await emit(page, PLATEAU, 12)
  await expect(trigger(page)).toBeEnabled()
})

test('position indisponible : explication et « Réessayer », déclencheur inactif', async ({
  page,
}) => {
  await openCapture(page)
  await fail(page, POSITION_UNAVAILABLE)
  await expect(page.getByText(fr.capture.position.unavailable)).toBeVisible()
  await expect(page.getByRole('button', { name: fr.capture.retry })).toBeVisible()
  await expect(trigger(page)).toBeDisabled()
  await expectNoSeriousViolations(page)
})

test('mesure manquée après une bonne Position : la Position récente reste utilisable', async ({
  page,
}) => {
  await openCapture(page)
  await emit(page, PLATEAU, 12)
  await expect(trigger(page)).toBeEnabled()

  await fail(page, POSITION_UNAVAILABLE)
  await expect(page.getByText(detected(12))).toBeVisible()
  await expect(page.getByText(fr.capture.position.unavailable)).toHaveCount(0)
  await expect(trigger(page)).toBeEnabled()
  await expectNoSeriousViolations(page)
})

test('refus après une bonne Position : explication, déclencheur inactif', async ({ page }) => {
  await openCapture(page)
  await emit(page, PLATEAU, 12)
  await expect(trigger(page)).toBeEnabled()

  await fail(page, PERMISSION_DENIED)
  await expect(page.getByText(fr.capture.position.denied)).toBeVisible()
  await expect(page.getByText(detected(12))).toHaveCount(0)
  await expect(trigger(page)).toBeDisabled()
  await expectNoSeriousViolations(page)
})

test('« Continuer quand même » est oublié hors Zone et après « Réessayer »', async ({ page }) => {
  await openCapture(page)
  const invitation = page.getByText(fr.capture.position.wait)
  const continueAnyway = page.getByRole('button', { name: fr.capture.position.continue })

  await emit(page, PLATEAU, 80)
  await continueAnyway.click()
  await expect(trigger(page)).toBeEnabled()

  // Sortie de la Zone puis retour, encore imprécis : nouvelle invitation.
  await emit(page, THIES, 80)
  await expect(page.getByText(fr.capture.zone.outside)).toBeVisible()
  await emit(page, PLATEAU, 80)
  await expect(invitation).toBeVisible()
  await expect(trigger(page)).toBeDisabled()

  // Continuer, puis refus et « Réessayer » : la Position suivante, imprécise, réinvite.
  await continueAnyway.click()
  await expect(trigger(page)).toBeEnabled()
  await fail(page, PERMISSION_DENIED)
  await page.getByRole('button', { name: fr.capture.retry }).click()
  await expectWatching(page)
  await emit(page, PLATEAU, 80)
  await expect(invitation).toBeVisible()
  await expect(trigger(page)).toBeDisabled()
})

test('la région annoncée ne change qu’avec le type d’état, pas à chaque mesure', async ({
  page,
}) => {
  await openCapture(page)
  const live = page.getByRole('status')
  await emit(page, PLATEAU, 12)
  await expect(page.getByText(detected(12))).toBeVisible()
  const announced = await live.textContent()
  expect(announced).not.toContain('12')
  await emit(page, PLATEAU, 9)
  await expect(page.getByText(detected(9))).toBeVisible()
  await expect(live).toHaveText(announced ?? '')
})

test('hors ligne : la configuration gardée dans Dexie est utilisée', async ({ page, capture }) => {
  await openCapture(page)
  await emit(page, PLATEAU, 12)
  await expect(trigger(page)).toBeEnabled()

  capture.setNetwork('offline')
  const before = capture.configRequests()
  await page.reload()
  await expectWatching(page)
  await emit(page, PLATEAU, 12)
  await expect(page.getByText(detected(12))).toBeVisible()
  await expect(trigger(page)).toBeEnabled()
  expect(capture.configRequests()).toBeGreaterThan(before)

  await expectNoSeriousViolations(page)

  await emit(page, THIES, 12)
  await expect(page.getByText(fr.capture.zone.outside)).toBeVisible()
})

test('première fois hors ligne : « connexion nécessaire une première fois » et « Réessayer »', async ({
  page,
  capture,
}) => {
  capture.setNetwork('offline')
  await openCapture(page)
  await emit(page, PLATEAU, 12)
  await expect(page.getByText(fr.capture.zone.firstConnection)).toBeVisible()
  await expect(trigger(page)).toBeDisabled()
  await expectNoSeriousViolations(page)

  capture.setNetwork('online')
  await page.getByRole('button', { name: fr.capture.retry }).click()
  await expect(page.getByText(detected(12))).toBeVisible()
  await expect(trigger(page)).toBeEnabled()
})

test('quitter l’écran arrête le suivi de la Position', async ({ page }) => {
  await openCapture(page)
  await page.getByRole('link', { name: /accueil/i }).click()
  await expect.poll(() => page.evaluate(() => window.__geo?.watchers() ?? -1)).toBe(0)
})
