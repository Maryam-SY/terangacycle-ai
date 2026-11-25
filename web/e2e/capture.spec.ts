// Stories 1.8 et 1.9 : écran 2 · Capture. Position et Zone active avant la photo (1.8),
// puis photo prise, allégée et nettoyée sur l'appareil, gardée en brouillon (1.9).
// Une ligne des matrices I/O des specs par test, en 390×844 sur la PWA construite.
// Géolocalisation simulée (pilotée par le test), GET /v1/config intercepté (Zone de
// test, pas les données OSM), audit axe à chaque état, aucune coordonnée en console et
// aucune requête hors de la coquille et de /v1/config.
import { createHash } from 'node:crypto'
import { readFileSync } from 'node:fs'

import AxeBuilder from '@axe-core/playwright'
import { test as base, expect, type Locator, type Page, type Route } from '@playwright/test'

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
    rule: { title: string; body: string }
    photo: {
      unreadable: string
      stale: string
      position: string
      alt: string
      retake: string
      continue: string
      saveError: string
    }
  }
  details: { title: string; photoAlt: string; position: string; back: string }
}

const fr = JSON.parse(
  readFileSync(new URL('../src/i18n/fr.json', import.meta.url), 'utf8'),
) as Texts

const CAPTURE_URL = /\/signaler\/capture$/
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
        // Viseur dans la page (getUserMedia) : jamais demandé, la prise de vue passe par
        // l'appareil photo natif (story 1.9).
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
  // `exact` : « Reprendre la photo » contient aussi « prendre la photo ».
  return page.getByRole('button', { name: fr.capture.trigger, exact: true })
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

  // Le déclencheur ouvre le sélecteur de prise de vue (un seul fichier), jamais
  // getUserMedia.
  const chooser = page.waitForEvent('filechooser')
  await trigger(page).click()
  expect((await chooser).isMultiple()).toBe(false)
  expect(await page.evaluate(() => window.__cameraCalls)).toBe(0)
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

// ---------------------------------------------------------------------------------------
// Story 1.9 : photographier le dépôt en version légère et sans métadonnées.
// ---------------------------------------------------------------------------------------

const DETAILS_URL = /\/signaler\/details$/
const MAX_PHOTO_BYTES = 307_200
const MAX_EDGE_PX = 1600
// Seconde mesure, reçue pendant la prise de vue : c'est elle qui est gardée.
const PLATEAU_LATER = { lat: 14.6712, lng: -17.4377 }

interface PhotoFile {
  name: string
  mimeType: string
  buffer: Buffer
}

/** Image fabriquée par un canevas du navigateur, rendue au test. `noisy` : dégradé et
 *  bruit, pour un poids proche d'une vraie photo de téléphone. */
async function canvasImage(
  page: Page,
  options: { width: number; height: number; type: 'image/jpeg' | 'image/png'; noisy: boolean },
): Promise<Buffer> {
  const base64 = await page.evaluate(async ({ width, height, type, noisy }) => {
    const canvas = document.createElement('canvas')
    canvas.width = width
    canvas.height = height
    const context = canvas.getContext('2d')
    if (!context) throw new Error('canevas indisponible')
    const image = context.createImageData(width, height)
    const { data } = image
    let seed = 7
    for (let pixel = 0; pixel < width * height; pixel += 1) {
      const x = pixel % width
      const y = Math.floor(pixel / width)
      let noise = 0
      if (noisy) {
        seed = (seed * 1103515245 + 12345) & 0x7fffffff
        noise = (seed >> 16) & 0x1f
      }
      const at = pixel * 4
      data[at] = Math.min(255, Math.round((x / width) * 200) + noise)
      data[at + 1] = Math.min(255, Math.round((y / height) * 200) + noise)
      data[at + 2] = Math.min(255, 90 + noise)
      data[at + 3] = 255
    }
    context.putImageData(image, 0, 0)
    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, type, 0.92))
    if (!blob) throw new Error('encodage impossible')
    canvas.width = 0
    canvas.height = 0
    return new Promise<string>((resolve, reject) => {
      const reader = new FileReader()
      reader.onerror = () => reject(reader.error)
      reader.onload = () => resolve(String(reader.result).split(',')[1] ?? '')
      reader.readAsDataURL(blob)
    })
  }, options)
  return Buffer.from(base64, 'base64')
}

/** Segment APP1 Exif construit à la main (TIFF gros-boutiste) : Orientation = 6 (pivoter
 *  de 90° dans le sens horaire) et GPS (14°40'15" N, 17°26'17" O). */
function exifApp1(): Buffer {
  const tiff = Buffer.alloc(140)
  tiff.write('MM', 0, 'latin1')
  tiff.writeUInt16BE(42, 2)
  tiff.writeUInt32BE(8, 4)
  const entry = (at: number, tag: number, type: number, count: number, value: Buffer) => {
    tiff.writeUInt16BE(tag, at)
    tiff.writeUInt16BE(type, at + 2)
    tiff.writeUInt32BE(count, at + 4)
    value.copy(tiff, at + 8)
  }
  const u32 = (value: number) => {
    const buffer = Buffer.alloc(4)
    buffer.writeUInt32BE(value)
    return buffer
  }
  // IFD0 (offset 8) : Orientation, pointeur vers l'IFD GPS (offset 38).
  tiff.writeUInt16BE(2, 8)
  entry(10, 0x0112, 3, 1, Buffer.from([0, 6, 0, 0]))
  entry(22, 0x8825, 4, 1, u32(38))
  tiff.writeUInt32BE(0, 34)
  // IFD GPS (offset 38) : références et rationnels (données à 92 et 116).
  tiff.writeUInt16BE(4, 38)
  entry(40, 0x0001, 2, 2, Buffer.from('N\0', 'latin1'))
  entry(52, 0x0002, 5, 3, u32(92))
  entry(64, 0x0003, 2, 2, Buffer.from('W\0', 'latin1'))
  entry(76, 0x0004, 5, 3, u32(116))
  tiff.writeUInt32BE(0, 88)
  ;[14, 1, 40, 1, 15, 1, 17, 1, 26, 1, 17, 1].forEach((value, index) =>
    tiff.writeUInt32BE(value, 92 + index * 4),
  )
  const payload = Buffer.concat([Buffer.from('Exif\0\0', 'latin1'), tiff])
  const header = Buffer.alloc(4)
  header.writeUInt16BE(0xffe1, 0)
  header.writeUInt16BE(payload.length + 2, 2)
  return Buffer.concat([header, payload])
}

/** Photo « de téléphone » : JPEG de 4000 × 3000 (12 Mpx), paysage tel qu'encodé, avec un
 *  APP1 Exif (orientation 6 et GPS) placé juste après SOI. */
async function cameraPhoto(page: Page): Promise<Buffer> {
  const jpeg = await canvasImage(page, { width: 4000, height: 3000, type: 'image/jpeg', noisy: true })
  return Buffer.concat([jpeg.subarray(0, 2), exifApp1(), jpeg.subarray(2)])
}

/** Codes des marqueurs d'en-tête d'un JPEG, de SOI à SOS (parcours indépendant de l'app). */
function headerMarkers(bytes: Buffer): number[] {
  expect(bytes.readUInt16BE(0)).toBe(0xffd8)
  expect(bytes.readUInt16BE(bytes.length - 2)).toBe(0xffd9)
  const markers: number[] = []
  let offset = 2
  for (;;) {
    expect(bytes[offset]).toBe(0xff)
    const marker = bytes[offset + 1]
    markers.push(marker)
    if (marker === 0xda) return markers
    offset += 2 + bytes.readUInt16BE(offset + 2)
    expect(offset).toBeLessThan(bytes.length)
  }
}

function sha256(bytes: Buffer): string {
  return createHash('sha256').update(bytes).digest('hex')
}

function rule(page: Page) {
  return page.getByRole('heading', { level: 2, name: fr.capture.rule.title })
}

function preview(page: Page) {
  return page.getByRole('img', { name: fr.capture.photo.alt })
}

function fileInput(page: Page) {
  return page.locator('input[type="file"]')
}

/** Déclencheur, puis le fichier remis par le sélecteur de prise de vue. */
async function takePhoto(page: Page, file: PhotoFile) {
  const chooser = page.waitForEvent('filechooser')
  await trigger(page).click()
  await (await chooser).setFiles(file)
}

/** Fichier remis directement à l'`<input>`, avec la date de modification voulue (le
 *  sélecteur de Playwright date toujours le fichier de l'instant). */
async function dropFile(page: Page, file: PhotoFile, lastModified: number) {
  await fileInput(page).evaluate(
    (input: HTMLInputElement, { base64, name, type, lastModified }) => {
      const bytes = Uint8Array.from(atob(base64), (char) => char.charCodeAt(0))
      const transfer = new DataTransfer()
      transfer.items.add(new File([bytes], name, { type, lastModified }))
      input.files = transfer.files
      input.dispatchEvent(new Event('change', { bubbles: true }))
    },
    { base64: file.buffer.toString('base64'), name: file.name, type: file.mimeType, lastModified },
  )
}

/** Octets (base64) et dimensions de l'image affichée par `<img>`. */
function imageBytes(image: Locator) {
  return image.evaluate(async (element: HTMLImageElement) => {
    await element.decode()
    // Octets de l'URL blob: de l'aperçu (XHR : `fetch` est réservé à src/api et src/offline).
    const blob = await new Promise<Blob>((resolve, reject) => {
      const request = new XMLHttpRequest()
      request.responseType = 'blob'
      request.onload = () => resolve(request.response as Blob)
      request.onerror = () => reject(new Error('aperçu illisible'))
      request.open('GET', element.src)
      request.send()
    })
    const base64 = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader()
      reader.onerror = () => reject(reader.error)
      reader.onload = () => resolve(String(reader.result).split(',')[1] ?? '')
      reader.readAsDataURL(blob)
    })
    return { base64, width: element.naturalWidth, height: element.naturalHeight }
  })
}

interface StoredDraft {
  base64: string
  type: string
  width: number
  height: number
  lat: unknown
  lng: unknown
  accuracy: unknown
  capturedAt: unknown
}

/** `meta.draft` lu sans Dexie ; `null` s'il n'existe pas. */
function readDraft(page: Page): Promise<StoredDraft | null> {
  return page.evaluate(async (name) => {
    const databases = await indexedDB.databases()
    if (!databases.some((database) => database.name === name)) return null
    const row = await new Promise<{ value?: Record<string, unknown> } | undefined>(
      (resolve, reject) => {
        const open = indexedDB.open(name)
        open.onerror = () => reject(open.error)
        open.onsuccess = () => {
          const database = open.result
          const request = database.transaction('meta', 'readonly').objectStore('meta').get('draft')
          request.onsuccess = () => {
            database.close()
            resolve(request.result as { value?: Record<string, unknown> } | undefined)
          }
          request.onerror = () => {
            database.close()
            reject(request.error)
          }
        }
      },
    )
    if (!row?.value) return null
    const { photo, lat, lng, accuracy, capturedAt } = row.value
    if (!(photo instanceof Blob)) throw new Error('photo du brouillon : pas un Blob')
    const bitmap = await createImageBitmap(photo)
    const size = { width: bitmap.width, height: bitmap.height }
    bitmap.close()
    const base64 = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader()
      reader.onerror = () => reject(reader.error)
      reader.onload = () => resolve(String(reader.result).split(',')[1] ?? '')
      reader.readAsDataURL(photo)
    })
    return { base64, type: photo.type, ...size, lat, lng, accuracy, capturedAt }
  }, 'terangacycle')
}

/** Écran 2 prêt : consentement, Position bonne dans la Zone. */
async function readyToShoot(page: Page) {
  await openCapture(page)
  await emit(page, PLATEAU, 12)
  await expect(trigger(page)).toBeEnabled()
}

test('déclencheur : <input accept="image/*" capture="environment">, cible ≥ 44 px, consigne visible', async ({
  page,
}) => {
  await readyToShoot(page)
  await expect(fileInput(page)).toHaveAttribute('accept', 'image/*')
  await expect(fileInput(page)).toHaveAttribute('capture', 'environment')
  await expect(fileInput(page)).not.toHaveAttribute('multiple')
  await expect(fileInput(page)).toBeEnabled()
  const box = await trigger(page).boundingBox()
  expect(box?.height).toBeGreaterThanOrEqual(44)
  expect(box?.width).toBeGreaterThanOrEqual(44)
  // Pictogramme et libellé.
  await expect(trigger(page).locator('svg')).toHaveCount(1)
  await expect(rule(page)).toBeVisible()
  await expect(page.getByText(fr.capture.rule.body)).toBeVisible()
  await expectNoSeriousViolations(page)
})

test('photo normale (12 Mpx, Exif avec GPS, orientation 6) : aperçu portrait, JPEG ≤ 300 Ko sans APP1, brouillon identique', async ({
  page,
}) => {
  await readyToShoot(page)
  const photo = await cameraPhoto(page)
  expect(photo.length).toBeGreaterThan(1_000_000)
  expect(photo.includes('Exif')).toBe(true)

  const chooser = page.waitForEvent('filechooser')
  await trigger(page).click()
  // La Position change pendant la prise de vue : la dernière mesure est gardée.
  await emit(page, PLATEAU_LATER, 9)
  const before = Date.now()
  await (await chooser).setFiles({ name: 'IMG_0001.jpg', mimeType: 'image/jpeg', buffer: photo })

  await expect(preview(page)).toBeVisible({ timeout: 20_000 })
  await expect(preview(page)).toBeFocused()
  await expect(rule(page)).toHaveCount(0)
  await expect(trigger(page)).toHaveCount(0)
  const shown = await imageBytes(preview(page))
  // Orientation 6 appliquée : le paysage de 4000 × 3000 devient un portrait.
  expect(shown.height).toBeGreaterThan(shown.width)
  expect(shown.height).toBeLessThanOrEqual(MAX_EDGE_PX)
  const shownBytes = Buffer.from(shown.base64, 'base64')
  expect(shownBytes.length).toBeLessThanOrEqual(MAX_PHOTO_BYTES)
  expect(headerMarkers(shownBytes)).not.toContain(0xe1)
  await expectNoSeriousViolations(page)
  // Rien n'est gardé avant « Continuer ».
  expect(await readDraft(page)).toBeNull()

  await page.getByRole('button', { name: fr.capture.photo.continue }).click()
  await expect(page).toHaveURL(DETAILS_URL)
  await expect(page.getByRole('heading', { level: 1, name: fr.details.title })).toBeVisible()
  await expect(page.getByRole('img', { name: fr.details.photoAlt })).toBeVisible()
  await expect(page.getByText(fr.details.position.replace('{{accuracy}}', '9'))).toBeVisible()

  const draft = await readDraft(page)
  expect(draft).not.toBeNull()
  const stored = Buffer.from(draft?.base64 ?? '', 'base64')
  expect(draft?.type).toBe('image/jpeg')
  expect(stored.length).toBeLessThanOrEqual(MAX_PHOTO_BYTES)
  // Aucun segment APP1 (Exif, XMP), aucune trace de l'Exif d'origine.
  expect(headerMarkers(stored)).not.toContain(0xe1)
  expect(stored.includes('Exif')).toBe(false)
  expect(stored.includes('http://ns.adobe.com/xap')).toBe(false)
  // Les octets gardés sont exactement ceux de l'aperçu.
  expect(sha256(stored)).toBe(sha256(shownBytes))
  expect(draft?.height).toBeGreaterThan(draft?.width ?? Infinity)
  expect(Math.max(draft?.width ?? 0, draft?.height ?? 0)).toBeLessThanOrEqual(MAX_EDGE_PX)
  // Position, précision et heure de la prise.
  expect(draft).toMatchObject({ lat: PLATEAU_LATER.lat, lng: PLATEAU_LATER.lng, accuracy: 9 })
  const capturedAt = Date.parse(String(draft?.capturedAt))
  expect(capturedAt).toBeGreaterThanOrEqual(before - 1000)
  expect(capturedAt).toBeLessThanOrEqual(Date.now() + 1000)
  expect(String(draft?.capturedAt)).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/)
  await expectNoSeriousViolations(page)

  // Retour à la capture : nouvelle prise possible.
  await page.getByRole('link', { name: fr.details.back }).click()
  await expect(page).toHaveURL(CAPTURE_URL)
})

test('image lisible non JPEG (comme un HEIC lu par le navigateur) : convertie en JPEG', async ({
  page,
}) => {
  await readyToShoot(page)
  const png = await canvasImage(page, { width: 1200, height: 900, type: 'image/png', noisy: false })
  await takePhoto(page, { name: 'photo.png', mimeType: 'image/png', buffer: png })
  await expect(preview(page)).toBeVisible()
  const shown = await imageBytes(preview(page))
  const bytes = Buffer.from(shown.base64, 'base64')
  expect(headerMarkers(bytes)).not.toContain(0xe1)
  expect({ width: shown.width, height: shown.height }).toEqual({ width: 1200, height: 900 })

  await page.getByRole('button', { name: fr.capture.photo.continue }).click()
  await expect(page).toHaveURL(DETAILS_URL)
  const draft = await readDraft(page)
  expect(draft?.type).toBe('image/jpeg')
  expect(sha256(Buffer.from(draft?.base64 ?? '', 'base64'))).toBe(sha256(bytes))
})

for (const [label, file] of [
  [
    'octets corrompus',
    {
      name: 'IMG_0002.jpg',
      mimeType: 'image/jpeg',
      buffer: Buffer.concat([Buffer.from([0xff, 0xd8, 0xff, 0xe0]), Buffer.alloc(4096, 0x5a)]),
    },
  ],
  [
    'HEIC non pris en charge',
    {
      name: 'IMG_0003.HEIC',
      mimeType: 'image/heic',
      buffer: Buffer.concat([
        Buffer.from([0, 0, 0, 0x18]),
        Buffer.from('ftypheic\0\0\0\0mif1heic', 'latin1'),
        Buffer.alloc(4096, 0x11),
      ]),
    },
  ],
] as const) {
  test(`fichier illisible (${label}) : « Cette photo n’a pas pu être lue. Reprenez-la. », aucun brouillon`, async ({
    page,
  }) => {
    await readyToShoot(page)
    await takePhoto(page, { ...file, buffer: Buffer.from(file.buffer) })
    await expect(page.getByText(fr.capture.photo.unreadable)).toBeVisible()
    // Le message est lu : le focus y est placé (le déclencheur, désactivé pendant le
    // traitement, ne le garde pas).
    await expect(page.getByText(fr.capture.photo.unreadable)).toBeFocused()
    await expect(preview(page)).toHaveCount(0)
    expect(await readDraft(page)).toBeNull()
    // On peut reprendre la photo tout de suite, consigne visible.
    await expect(trigger(page)).toBeEnabled()
    await expect(rule(page)).toBeVisible()
    await expectNoSeriousViolations(page)
  })
}

test('photo ancienne (plus de 10 minutes) : refusée avec un message, aucun brouillon', async ({
  page,
}) => {
  await readyToShoot(page)
  const jpeg = await canvasImage(page, { width: 800, height: 600, type: 'image/jpeg', noisy: false })
  await dropFile(
    page,
    { name: 'galerie.jpg', mimeType: 'image/jpeg', buffer: jpeg },
    Date.now() - 11 * 60_000,
  )
  await expect(page.getByText(fr.capture.photo.stale)).toBeVisible()
  await expect(preview(page)).toHaveCount(0)
  expect(await readDraft(page)).toBeNull()
  await expect(trigger(page)).toBeEnabled()
  await expectNoSeriousViolations(page)

  // La même image, prise à l'instant : acceptée.
  await dropFile(page, { name: 'photo.jpg', mimeType: 'image/jpeg', buffer: jpeg }, Date.now())
  await expect(preview(page)).toBeVisible()
  await expect(page.getByText(fr.capture.photo.stale)).toHaveCount(0)
})

test('reprise : « Reprendre la photo » efface l’aperçu, la consigne revient, déclencheur actif', async ({
  page,
}) => {
  await readyToShoot(page)
  const jpeg = await canvasImage(page, { width: 800, height: 600, type: 'image/jpeg', noisy: false })
  await takePhoto(page, { name: 'photo.jpg', mimeType: 'image/jpeg', buffer: jpeg })
  await expect(preview(page)).toBeVisible()
  await expect(rule(page)).toHaveCount(0)

  await page.getByRole('button', { name: fr.capture.photo.retake }).click()
  await expect(preview(page)).toHaveCount(0)
  await expect(rule(page)).toBeVisible()
  await expect(trigger(page)).toBeEnabled()
  await expect(trigger(page)).toBeFocused()
  expect(await readDraft(page)).toBeNull()
  await expectNoSeriousViolations(page)

  // Seconde prise : nouvel aperçu.
  await takePhoto(page, { name: 'photo-2.jpg', mimeType: 'image/jpeg', buffer: jpeg })
  await expect(preview(page)).toBeVisible()
})

test('lien direct /signaler/details sans brouillon : redirection vers la capture', async ({
  page,
}) => {
  await openCapture(page)
  await page.goto('/signaler/details')
  await expect(page).toHaveURL(CAPTURE_URL)
  await expect(page.getByRole('heading', { level: 1, name: fr.capture.title })).toBeVisible()
})

test('déclencheur inactif (hors Zone, imprécise) : aucune prise de vue possible', async ({
  page,
}) => {
  await openCapture(page)
  await emit(page, THIES, 10)
  await expect(page.getByText(fr.capture.zone.outside)).toBeVisible()
  await expect(trigger(page)).toBeDisabled()
  await expect(rule(page)).toBeVisible()

  await emit(page, PLATEAU, 80)
  await expect(page.getByText(fr.capture.position.wait)).toBeVisible()
  await expect(trigger(page)).toBeDisabled()
  await expectNoSeriousViolations(page)
  // Le déclencheur désactivé n'ouvre pas le sélecteur, même cliqué de force.
  let opened = false
  page.on('filechooser', () => {
    opened = true
  })
  await trigger(page).click({ force: true })
  await page.waitForTimeout(300)
  expect(opened).toBe(false)
})

test('Position imprécise au retour de l’appareil photo : photo acceptée avec cette précision', async ({
  page,
}) => {
  await readyToShoot(page)
  const jpeg = await canvasImage(page, { width: 800, height: 600, type: 'image/jpeg', noisy: false })
  const chooser = page.waitForEvent('filechooser')
  await trigger(page).click()
  await emit(page, PLATEAU, 80)
  await (await chooser).setFiles({ name: 'photo.jpg', mimeType: 'image/jpeg', buffer: jpeg })
  await expect(preview(page)).toBeVisible()
  await page.getByRole('button', { name: fr.capture.photo.continue }).click()
  await expect(page).toHaveURL(DETAILS_URL)
  expect(await readDraft(page)).toMatchObject({ accuracy: 80 })
})

test('Position sortie de la Zone pendant la prise de vue : photo refusée, aucun brouillon', async ({
  page,
}) => {
  await readyToShoot(page)
  const jpeg = await canvasImage(page, { width: 800, height: 600, type: 'image/jpeg', noisy: false })
  const chooser = page.waitForEvent('filechooser')
  await trigger(page).click()
  await emit(page, THIES, 10)
  await (await chooser).setFiles({ name: 'photo.jpg', mimeType: 'image/jpeg', buffer: jpeg })
  await expect(page.getByText(fr.capture.photo.position)).toBeVisible()
  await expect(preview(page)).toHaveCount(0)
  expect(await readDraft(page)).toBeNull()
  await expectNoSeriousViolations(page)
})

test('Position mesurée il y a plus de 2 minutes à l’arrivée du fichier : photo refusée, aucun brouillon', async ({
  page,
}) => {
  await page.clock.install()
  await readyToShoot(page)
  const jpeg = await canvasImage(page, { width: 800, height: 600, type: 'image/jpeg', noisy: false })
  const chooser = page.waitForEvent('filechooser')
  await trigger(page).click()
  // Le suivi de la Position s'est arrêté pendant que l'appareil photo était ouvert.
  await page.clock.fastForward('02:01')
  await (await chooser).setFiles({ name: 'photo.jpg', mimeType: 'image/jpeg', buffer: jpeg })
  await expect(page.getByText(fr.capture.photo.position)).toBeVisible()
  await expect(page.getByText(fr.capture.photo.position)).toBeFocused()
  await expect(preview(page)).toHaveCount(0)
  expect(await readDraft(page)).toBeNull()
})

test('une nouvelle photo efface l’ancien brouillon, même refusée', async ({ page }) => {
  await readyToShoot(page)
  const jpeg = await canvasImage(page, { width: 800, height: 600, type: 'image/jpeg', noisy: false })
  await takePhoto(page, { name: 'photo.jpg', mimeType: 'image/jpeg', buffer: jpeg })
  await expect(preview(page)).toBeVisible()
  await page.getByRole('button', { name: fr.capture.photo.continue }).click()
  await expect(page).toHaveURL(DETAILS_URL)
  expect(await readDraft(page)).not.toBeNull()

  await page.getByRole('link', { name: fr.details.back }).click()
  await expect(page).toHaveURL(CAPTURE_URL)
  await expectWatching(page)
  await emit(page, PLATEAU, 12)
  await expect(trigger(page)).toBeEnabled()
  await dropFile(
    page,
    { name: 'galerie.jpg', mimeType: 'image/jpeg', buffer: jpeg },
    Date.now() - 11 * 60_000,
  )
  await expect(page.getByText(fr.capture.photo.stale)).toBeVisible()
  await expect.poll(() => readDraft(page)).toBeNull()

  await page.goto('/signaler/details')
  await expect(page).toHaveURL(CAPTURE_URL)
})

test('« Continuer » quand le brouillon ne peut pas être gardé : message, on reste sur la capture', async ({
  page,
}) => {
  await readyToShoot(page)
  const jpeg = await canvasImage(page, { width: 800, height: 600, type: 'image/jpeg', noisy: false })
  await takePhoto(page, { name: 'photo.jpg', mimeType: 'image/jpeg', buffer: jpeg })
  await expect(preview(page)).toBeVisible()

  await page.evaluate(() => {
    IDBObjectStore.prototype.put = () => {
      throw new DOMException('espace saturé (test)', 'QuotaExceededError')
    }
  })
  const keep = page.getByRole('button', { name: fr.capture.photo.continue })
  await keep.click()

  await expect(page.getByText(fr.capture.photo.saveError)).toBeVisible()
  await expect(page.getByText(fr.capture.photo.saveError)).toBeFocused()
  await expect(page).toHaveURL(CAPTURE_URL)
  await expect(keep).toBeEnabled()
  await expect(preview(page)).toBeVisible()
  expect(await readDraft(page)).toBeNull()
  await expectNoSeriousViolations(page)
})
