// Story 1.13 : écran 3 · Détails (Taille de tas, Type de déchet, commentaire, envoi) et
// écran 4 · Confirmation (Numéro de suivi, Frise de suivi). Une ligne de la matrice I/O de
// la spec par test, en 390×844 sur la PWA construite.
// Parcours réel jusqu'à l'écran 3 (consentement, Position simulée, photo d'un canevas),
// GET /v1/config et POST /v1/reports interceptés (aucune API réelle). Le corps envoyé est
// lu dans la page par un espion de `fetch` (meta, octets de la photo, en-têtes). Audit axe
// à chaque état, aucun débordement horizontal, cibles ≥ 44 px, aucune coordonnée en console.
import { createHash } from 'node:crypto'
import { readFileSync } from 'node:fs'

import AxeBuilder from '@axe-core/playwright'
import { test as base, expect, type Page, type Route } from '@playwright/test'

/** Requête POST /v1/reports vue par l'espion de `fetch`, dans la page. */
interface SentReport {
  meta: string
  metaIsText: boolean
  photoName: string
  photoType: string
  photoBase64: string
  deviceId: string | null
  authorization: string | null
  contentType: string | null
}

declare global {
  interface Window {
    __reportGeo?: {
      watchers: () => number
      emit: (lat: number, lng: number, accuracy: number) => void
    }
    __sentReports?: SentReport[]
  }
}

interface Texts {
  app: { name: string }
  consent: { title: string; accept: string; training: { label: string } }
  capture: { title: string; trigger: string; photo: { continue: string } }
  details: {
    title: string
    photoAlt: string
    send: string
    retry: string
    networkError: string
    backToCapture: string
    retake: string
    missing: { heapSize: string }
    comment: { label: string }
  }
  heapSize: { small: string; medium: string; large: string }
  wasteType: { plastic: string; metal: string; glass: string }
  confirmation: { title: string; trackingLabel: string; demo: string; home: string }
  timeline: { reported: string; validated: string; assigned: string; collected: string; current: string }
  errors: Record<string, string>
}

const fr = JSON.parse(
  readFileSync(new URL('../src/i18n/fr.json', import.meta.url), 'utf8'),
) as Texts

const DB_NAME = 'terangacycle'
const CAPTURE_URL = /\/signaler\/capture$/
const DETAILS_URL = /\/signaler\/details$/
const CONFIRMATION_URL = /\/signaler\/confirmation$/
const CONSENT_URL = /\/signaler\/consentement$/
const HOME_URL = /:\d+\/$/
const APP_ORIGIN = 'http://127.0.0.1:4173'
const UUID_V4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
const DEVICE_ID = /^[A-Za-z0-9_-]{43}$/
const TRACKING_NUMBER = 'TC-2026-000042'
const EMOJI = '🙏'

const ZONE_RING = [
  [-17.55, 14.65],
  [-17.4, 14.65],
  [-17.4, 14.8],
  [-17.55, 14.8],
  [-17.55, 14.65],
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
// Point témoin ; ses coordonnées ne doivent jamais apparaître dans la console.
const PLATEAU = { lat: 14.6708, lng: -17.4381 }
const COORDINATE_TEXTS = ['14.67', '17.43']

/** Réponse d'un POST /v1/reports : statut et corps JSON, page HTML sans enveloppe, ou
 *  coupure réseau. */
type Reply =
  | { status: number; json?: unknown }
  | { status: number; html: string }
  | 'offline'

function envelope(code: string): unknown {
  return { error: { code, message: 'message du serveur', request_id: 'req-e2e' } }
}

interface ReportServer {
  /** Réponses des prochains envois, dans l'ordre ; ensuite, le serveur simulé répond 201
   *  au premier envoi réussi, 200 aux suivants (renvoi du même Identifiant client). */
  queue: (...replies: Reply[]) => void
  /** `is_demo` des réponses du serveur simulé. */
  setDemo: (value: boolean) => void
  /** Délai avant chaque réponse, en millisecondes. */
  setDelay: (ms: number) => void
  /** Nombre de requêtes POST /v1/reports reçues. */
  requests: () => number
}

const test = base.extend<{ server: ReportServer }>({
  // Second argument nommé `provide` (et non `use`) : la règle rules-of-hooks le prendrait pour un hook.
  server: [
    async ({ page }, provide) => {
      await page.addInitScript(() => {
        const watchers = new Map<number, PositionCallback>()
        let nextId = 1
        const geolocation = {
          watchPosition(success: PositionCallback) {
            const id = nextId
            nextId += 1
            watchers.set(id, success)
            return id
          },
          clearWatch(id: number) {
            watchers.delete(id)
          },
          getCurrentPosition() {},
        }
        Object.defineProperty(navigator, 'geolocation', { configurable: true, get: () => geolocation })
        Object.defineProperty(window, '__reportGeo', {
          value: {
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
              for (const success of watchers.values()) success(position)
            },
          },
        })

        // Espion de `fetch` : copie de chaque POST /v1/reports, puis la requête suit. Copies
        // gardées dans sessionStorage : elles survivent à un rechargement de la page.
        const KEY = '__sentReports'
        let sent: SentReport[] = []
        try {
          sent = JSON.parse(sessionStorage.getItem(KEY) ?? '[]') as SentReport[]
        } catch {
          // Document sans sessionStorage (about:blank) : rien à reprendre.
        }
        Object.defineProperty(window, '__sentReports', { get: () => sent })
        // Espion posé par le test (dans la page), pas un appel de l'application : la règle
        // « pas de fetch hors de src/api/ » ne s'applique pas ici.
        // oxlint-disable-next-line no-restricted-properties
        const original = window.fetch.bind(window)
        // oxlint-disable-next-line no-restricted-properties
        window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
          const request = input instanceof Request ? input : new Request(input, init)
          if (new URL(request.url).pathname === '/v1/reports') {
            const form = await request.clone().formData()
            const meta = form.get('meta')
            const photo = form.get('photo') as File
            const bytes = new Uint8Array(await photo.arrayBuffer())
            let binary = ''
            for (const byte of bytes) binary += String.fromCharCode(byte)
            sent.push({
              meta: String(meta),
              metaIsText: typeof meta === 'string',
              photoName: photo.name,
              photoType: photo.type,
              photoBase64: btoa(binary),
              deviceId: request.headers.get('X-Device-Id'),
              authorization: request.headers.get('Authorization'),
              contentType: request.headers.get('Content-Type'),
            })
            sessionStorage.setItem(KEY, JSON.stringify(sent))
          }
          return original(request)
        }
      })

      await page.route('**/v1/config', (route: Route) => route.fulfill({ json: CONFIG }))

      const replies: Reply[] = []
      let demo = false
      let delay = 0
      let requests = 0
      let successes = 0
      await page.route('**/v1/reports', async (route: Route) => {
        requests += 1
        if (delay > 0) await new Promise((resolve) => setTimeout(resolve, delay))
        const reply = replies.shift()
        if (reply === 'offline') {
          await route.abort('internetdisconnected')
          return
        }
        if (reply && 'html' in reply) {
          await route.fulfill({ status: reply.status, contentType: 'text/html', body: reply.html })
          return
        }
        const created = {
          id: '3f0c2a8e-5b9d-4c71-8e2f-6a1b0c9d7e54',
          tracking_number: TRACKING_NUMBER,
          status: 'pending_review',
          received_at: '2026-11-26T10:00:05Z',
          is_demo: demo,
        }
        if (reply) {
          await route.fulfill({ status: reply.status, json: reply.json ?? created })
          return
        }
        await route.fulfill({ status: successes === 0 ? 201 : 200, json: created })
        successes += 1
      })

      const consoleMessages: string[] = []
      page.on('console', (message) => consoleMessages.push(message.text()))
      const outgoing: { method: string; url: string }[] = []
      page.context().on('request', (request) =>
        outgoing.push({ method: request.method(), url: request.url() }),
      )

      await provide({
        queue: (...more) => {
          replies.push(...more)
        },
        setDemo: (value) => {
          demo = value
        },
        setDelay: (ms) => {
          delay = ms
        },
        requests: () => requests,
      })

      // Ni coordonnée, ni Identifiant d'appareil, ni Numéro de suivi dans la console.
      const deviceIds = (await sentReports(page).catch(() => []))
        .map((report) => report.deviceId)
        .filter((id): id is string => Boolean(id))
      const secrets = [...COORDINATE_TEXTS, TRACKING_NUMBER, ...deviceIds]
      const leaked = consoleMessages.filter((text) => secrets.some((secret) => text.includes(secret)))
      expect(leaked).toEqual([])

      // Rien d'autre ne quitte la page que la coquille, GET /v1/config et POST /v1/reports.
      const unexpected = outgoing.filter(({ method, url }) => {
        const target = new URL(url)
        if (target.protocol === 'data:' || target.protocol === 'blob:') return false
        if (target.origin !== APP_ORIGIN) return true
        if (target.pathname === '/v1/reports') return method !== 'POST'
        if (method !== 'GET') return true
        return target.pathname.startsWith('/v1/') && target.pathname !== '/v1/config'
      })
      expect(unexpected).toEqual([])
    },
    { auto: true },
  ],
})

// ---------------------------------------------------------------------------------------
// Aides
// ---------------------------------------------------------------------------------------

/** JPEG de 800 × 600 fabriqué par un canevas du navigateur. */
async function canvasJpeg(page: Page): Promise<Buffer> {
  const base64 = await page.evaluate(async () => {
    const canvas = document.createElement('canvas')
    canvas.width = 800
    canvas.height = 600
    const context = canvas.getContext('2d')
    if (!context) throw new Error('canevas indisponible')
    const gradient = context.createLinearGradient(0, 0, 800, 600)
    gradient.addColorStop(0, 'rgb(40, 90, 60)')
    gradient.addColorStop(1, 'rgb(200, 180, 90)')
    context.fillStyle = gradient
    context.fillRect(0, 0, 800, 600)
    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.9))
    if (!blob) throw new Error('encodage impossible')
    return new Promise<string>((resolve, reject) => {
      const reader = new FileReader()
      reader.onerror = () => reject(reader.error)
      reader.onload = () => resolve(String(reader.result).split(',')[1] ?? '')
      reader.readAsDataURL(blob)
    })
  })
  return Buffer.from(base64, 'base64')
}

/** Parcours réel jusqu'à l'écran 3 : consentement (réentraînement accepté ou non),
 *  Position bonne au Plateau, photo prise puis gardée. */
async function openDetails(page: Page, { training = false }: { training?: boolean } = {}) {
  await page.goto('/signaler')
  if (training) await page.getByLabel(fr.consent.training.label).check()
  await page.getByRole('button', { name: fr.consent.accept }).click()
  await expect(page).toHaveURL(CAPTURE_URL)
  await expect.poll(() => page.evaluate(() => window.__reportGeo?.watchers() ?? 0)).toBe(1)
  await page.evaluate(({ lat, lng }) => window.__reportGeo?.emit(lat, lng, 12), PLATEAU)
  const trigger = page.getByRole('button', { name: fr.capture.trigger, exact: true })
  await expect(trigger).toBeEnabled()
  const jpeg = await canvasJpeg(page)
  const chooser = page.waitForEvent('filechooser')
  await trigger.click()
  await (await chooser).setFiles({ name: 'photo.jpg', mimeType: 'image/jpeg', buffer: jpeg })
  await page.getByRole('button', { name: fr.capture.photo.continue }).click()
  await expect(page).toHaveURL(DETAILS_URL)
  await expect(page.getByRole('heading', { level: 1, name: fr.details.title })).toBeVisible()
}

interface StoredDraft {
  base64: string
  clientUuid: unknown
  capturedAt: unknown
}

/** `meta.draft` lu sans Dexie ; `null` s'il n'existe pas. */
function readDraft(page: Page): Promise<StoredDraft | null> {
  return page.evaluate(async (name) => {
    const database = await new Promise<IDBDatabase>((resolve, reject) => {
      const open = indexedDB.open(name)
      open.onerror = () => reject(open.error)
      open.onsuccess = () => resolve(open.result)
    })
    const row = await new Promise<{ value?: Record<string, unknown> } | undefined>(
      (resolve, reject) => {
        const request = database.transaction('meta', 'readonly').objectStore('meta').get('draft')
        request.onsuccess = () => resolve(request.result as { value?: Record<string, unknown> })
        request.onerror = () => reject(request.error)
      },
    )
    database.close()
    if (!row?.value) return null
    const { photo, clientUuid, capturedAt } = row.value
    if (!(photo instanceof Blob)) throw new Error('photo du brouillon : pas un Blob')
    const base64 = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader()
      reader.onerror = () => reject(reader.error)
      reader.onload = () => resolve(String(reader.result).split(',')[1] ?? '')
      reader.readAsDataURL(photo)
    })
    return { base64, clientUuid, capturedAt }
  }, DB_NAME)
}

/** Modifie `meta[key]` sans Dexie : champs remplacés (`set`) ou retirés (`drop`). */
function patchMeta(
  page: Page,
  key: string,
  { set = {}, drop = [] }: { set?: Record<string, unknown>; drop?: string[] },
): Promise<void> {
  return page.evaluate(
    async ({ name, key, set, drop }) => {
      const database = await new Promise<IDBDatabase>((resolve, reject) => {
        const open = indexedDB.open(name)
        open.onerror = () => reject(open.error)
        open.onsuccess = () => resolve(open.result)
      })
      await new Promise<void>((resolve, reject) => {
        const transaction = database.transaction('meta', 'readwrite')
        const store = transaction.objectStore('meta')
        const request = store.get(key)
        request.onsuccess = () => {
          const row = request.result as { key: string; value: Record<string, unknown> }
          const value = { ...row.value, ...set }
          for (const field of drop) delete value[field]
          store.put({ key, value })
        }
        transaction.oncomplete = () => resolve()
        transaction.onerror = () => reject(transaction.error)
      })
      database.close()
    },
    { name: DB_NAME, key, set, drop },
  )
}

function sentReports(page: Page): Promise<SentReport[]> {
  return page.evaluate(() => [...(window.__sentReports ?? [])])
}

function sentMeta(report: SentReport): Record<string, unknown> {
  return JSON.parse(report.meta) as Record<string, unknown>
}

function sha256(base64: string): string {
  return createHash('sha256').update(Buffer.from(base64, 'base64')).digest('hex')
}

function radio(page: Page, name: string) {
  return page.getByRole('radio', { name })
}

/** Option (la carte cliquable) qui porte le bouton radio nommé. */
function option(page: Page, name: string) {
  return page.locator('label').filter({ has: radio(page, name) })
}

function sendButton(page: Page) {
  return page.getByRole('button', { name: fr.details.send })
}

function comment(page: Page) {
  return page.getByLabel(fr.details.comment.label)
}

async function expectNoSeriousViolations(page: Page) {
  const { violations } = await new AxeBuilder({ page }).analyze()
  const serious = violations
    .filter((violation) => violation.impact === 'critical' || violation.impact === 'serious')
    .map((violation) => `${violation.id} (${violation.impact}) : ${violation.help}`)
  expect(serious).toEqual([])
}

/** 390 px de large sans défilement horizontal ; toute cible tactile visible ≥ 44 × 44 px. */
async function expectMobileLayout(page: Page) {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  )
  expect(overflow).toBeLessThanOrEqual(0)
  const small = await page.evaluate(() =>
    [...document.querySelectorAll<HTMLElement>('button, a[href], textarea, label:has(input)')]
      .map((element) => {
        const box = element.getBoundingClientRect()
        return { text: (element.textContent ?? '').trim().slice(0, 40), width: box.width, height: box.height }
      })
      .filter((box) => (box.width > 0 || box.height > 0) && (box.width < 44 || box.height < 44)),
  )
  expect(small).toEqual([])
}

/** Écran 4 avec le Numéro de suivi et la Frise à l'étape « Signalé ». */
async function expectConfirmation(page: Page) {
  await expect(page).toHaveURL(CONFIRMATION_URL)
  await expect(page.getByRole('heading', { level: 1, name: fr.confirmation.title })).toBeVisible()
  await expect(page.getByText(TRACKING_NUMBER, { exact: true })).toBeVisible()
  const steps = page.getByRole('list').getByRole('listitem')
  await expect(steps).toHaveCount(4)
  const labels = [fr.timeline.reported, fr.timeline.validated, fr.timeline.assigned, fr.timeline.collected]
  for (const [index, label] of labels.entries()) await expect(steps.nth(index)).toContainText(label)
  await expect(steps.nth(0)).toHaveAttribute('aria-current', 'step')
  await expect(steps.nth(0)).toContainText(fr.timeline.current)
  await expect(page.locator('[aria-current="step"]')).toHaveCount(1)
}

// ---------------------------------------------------------------------------------------
// Matrice I/O de la story 1.13
// ---------------------------------------------------------------------------------------

test('nominal : Taille « moyen », sans Type ni commentaire → POST attendu, 201 → écran 4, brouillon effacé', async ({
  page,
  server,
}) => {
  await openDetails(page)
  // Miniature avec texte alternatif.
  await expect(page.getByRole('img', { name: fr.details.photoAlt })).toBeVisible()
  await expect(sendButton(page)).toBeDisabled()
  await expectNoSeriousViolations(page)
  await expectMobileLayout(page)
  // Aucune Taille ni aucun Type présélectionnés.
  await expect(page.getByRole('radio', { checked: true })).toHaveCount(0)

  const draft = await readDraft(page)
  expect(String(draft?.clientUuid)).toMatch(UUID_V4)
  await option(page, fr.heapSize.medium).click()
  await expect(radio(page, fr.heapSize.medium)).toBeChecked()
  await expect(sendButton(page)).toBeEnabled()
  await expectNoSeriousViolations(page)
  await sendButton(page).click()

  await expectConfirmation(page)
  await expect(page.getByText(fr.confirmation.demo)).toHaveCount(0)
  expect(server.requests()).toBe(1)
  const [sent] = await sentReports(page)
  expect(sent.metaIsText).toBe(true)
  expect(sentMeta(sent)).toEqual({
    client_uuid: draft?.clientUuid,
    lat: PLATEAU.lat,
    lng: PLATEAU.lng,
    accuracy_m: 12,
    captured_at: draft?.capturedAt,
    heap_size: 'medium',
    consent: { terms: true, training: false },
  })
  // Les octets exacts du JPEG de l'écran 2.
  expect(sha256(sent.photoBase64)).toBe(sha256(draft?.base64 ?? ''))
  expect(sent.photoName).toBe('photo.jpg')
  expect(sent.photoType).toBe('image/jpeg')
  expect(sent.contentType).toMatch(/^multipart\/form-data; boundary=/)
  expect(sent.deviceId).toMatch(DEVICE_ID)
  expect(sent.authorization).toBeNull()
  expect(await readDraft(page)).toBeNull()
  await expectNoSeriousViolations(page)
  await expectMobileLayout(page)

  // « Retour à l'accueil » : écran 1, brouillon toujours absent.
  await page.getByRole('button', { name: fr.confirmation.home }).click()
  await expect(page).toHaveURL(HOME_URL)
  await expect(page.getByRole('heading', { level: 1, name: fr.app.name })).toBeVisible()
  expect(await readDraft(page)).toBeNull()
})

test('complet : Type « plastique », commentaire de 280 points de code (emojis), 281e frappe ignorée', async ({
  page,
}) => {
  await openDetails(page)
  await option(page, fr.heapSize.large).click()
  await option(page, fr.wasteType.plastic).click()
  await expect(radio(page, fr.wasteType.plastic)).toBeChecked()

  // Collage trop long : tronqué à 280 points de code.
  await comment(page).fill(EMOJI.repeat(300))
  await expect(comment(page)).toHaveValue(EMOJI.repeat(280))
  await expect(page.getByText('280/280', { exact: true })).toBeVisible()
  // 281e frappe ignorée.
  await comment(page).press('End')
  await comment(page).pressSequentially('a')
  await expect(comment(page)).toHaveValue(EMOJI.repeat(280))
  await expect(page.getByText('280/280', { exact: true })).toBeVisible()
  await expectNoSeriousViolations(page)
  await expectMobileLayout(page)

  await sendButton(page).click()
  await expectConfirmation(page)
  const [sent] = await sentReports(page)
  expect(sentMeta(sent)).toMatchObject({
    heap_size: 'large',
    waste_type: 'plastic',
    comment: EMOJI.repeat(280),
  })
})

test('Type retiré : touché de nouveau, aucun Type choisi, waste_type absent', async ({ page }) => {
  await openDetails(page)
  await option(page, fr.heapSize.small).click()
  await option(page, fr.wasteType.metal).click()
  await expect(radio(page, fr.wasteType.metal)).toBeChecked()
  // Coche visible sur l'option choisie (état signalé autrement que par la couleur).
  await expect(option(page, fr.wasteType.metal).locator('svg')).toHaveCount(2)

  await option(page, fr.wasteType.metal).click()
  await expect(radio(page, fr.wasteType.metal)).not.toBeChecked()
  await expect(option(page, fr.wasteType.metal).locator('svg')).toHaveCount(1)
  await expect(page.getByRole('radio', { checked: true })).toHaveCount(1)
  await expectNoSeriousViolations(page)

  await sendButton(page).click()
  await expectConfirmation(page)
  const [sent] = await sentReports(page)
  expect(sentMeta(sent)).not.toHaveProperty('waste_type')
  expect(sentMeta(sent)).toMatchObject({ heap_size: 'small' })
})

test('Taille manquante : « Envoyer » désactivé, raison annoncée, aucune requête', async ({
  page,
  server,
}) => {
  await openDetails(page)
  await option(page, fr.wasteType.glass).click()
  await comment(page).fill('Au bord de la route')
  await expect(sendButton(page)).toBeDisabled()
  await expect(sendButton(page)).toHaveAccessibleDescription(fr.details.missing.heapSize)
  await expect(page.getByRole('status')).toHaveText(fr.details.missing.heapSize)
  await sendButton(page).click({ force: true })
  await page.waitForTimeout(300)
  expect(server.requests()).toBe(0)
  expect(await sentReports(page)).toEqual([])
  await expectNoSeriousViolations(page)
})

test('double appui : une seule requête, écran 4', async ({ page, server }) => {
  server.setDelay(800)
  await openDetails(page)
  await option(page, fr.heapSize.medium).click()
  await sendButton(page).dblclick()
  // Bouton désactivé pendant la requête.
  await expect(page.getByRole('button', { disabled: true })).toHaveCount(1)
  await expectConfirmation(page)
  expect(server.requests()).toBe(1)
  expect(await sentReports(page)).toHaveLength(1)
})

test('renvoi : échec réseau puis « Réessayer », même client_uuid, rechargement compris ; 200 → écran 4', async ({
  page,
  server,
}) => {
  server.queue('offline', 'offline', { status: 200 })
  await openDetails(page)
  const draft = await readDraft(page)
  await option(page, fr.heapSize.small).click()
  await comment(page).fill('Près du marché')
  await sendButton(page).click()

  const message = page.getByText(fr.details.networkError)
  await expect(message).toBeVisible()
  await expect(message).toBeFocused()
  // Saisie et brouillon gardés.
  await expect(radio(page, fr.heapSize.small)).toBeChecked()
  await expect(comment(page)).toHaveValue('Près du marché')
  expect((await readDraft(page))?.clientUuid).toBe(draft?.clientUuid)

  await page.getByRole('button', { name: fr.details.retry }).click()
  await expect(message).toBeVisible()
  expect(server.requests()).toBe(2)

  // Rechargement : nouvel écran, même brouillon, même Identifiant client.
  await page.reload()
  await expect(page.getByRole('heading', { level: 1, name: fr.details.title })).toBeVisible()
  await option(page, fr.heapSize.small).click()
  await sendButton(page).click()
  await expectConfirmation(page)

  const sent = await sentReports(page)
  expect(sent).toHaveLength(3)
  for (const report of sent) expect(sentMeta(report).client_uuid).toBe(draft?.clientUuid)
  expect(sentMeta(sent[0])).toMatchObject({ comment: 'Près du marché' })
})

test('démo : is_demo vrai → étiquette « Données de démonstration »', async ({ page, server }) => {
  server.setDemo(true)
  await openDetails(page)
  await option(page, fr.heapSize.medium).click()
  await sendButton(page).click()
  await expectConfirmation(page)
  await expect(page.getByText(fr.confirmation.demo, { exact: true })).toBeVisible()
  await expectNoSeriousViolations(page)
  await expectMobileLayout(page)
})

test('hors Zone : 422 outside_active_zone → son message et un lien vers l’écran 2', async ({
  page,
  server,
}) => {
  server.queue({ status: 422, json: envelope('outside_active_zone') })
  await openDetails(page)
  await option(page, fr.heapSize.medium).click()
  await sendButton(page).click()
  const message = page.getByText(fr.errors.outside_active_zone)
  await expect(message).toBeVisible()
  await expect(message).toBeFocused()
  expect(await readDraft(page)).not.toBeNull()
  await expectNoSeriousViolations(page)
  await expectMobileLayout(page)
  await page.getByRole('link', { name: fr.details.backToCapture }).click()
  await expect(page).toHaveURL(CAPTURE_URL)
})

test('consentement : 422 consent_required → écran de consentement', async ({ page, server }) => {
  server.queue({ status: 422, json: envelope('consent_required') })
  await openDetails(page)
  await option(page, fr.heapSize.medium).click()
  await sendButton(page).click()
  await expect(page).toHaveURL(CONSENT_URL)
  await expect(page.getByRole('heading', { level: 1, name: fr.consent.title })).toBeVisible()
})

for (const [status, code] of [
  [413, 'photo_too_large'],
  [415, 'unsupported_media_type'],
  [422, 'photo_unreadable'],
] as const) {
  test(`photo : ${status} ${code} → message et invitation à reprendre la photo`, async ({
    page,
    server,
  }) => {
    server.queue({ status, json: envelope(code) })
    await openDetails(page)
    await option(page, fr.heapSize.medium).click()
    await sendButton(page).click()
    const message = page.getByText(fr.errors[code])
    await expect(message).toBeVisible()
    await expect(message).toBeFocused()
    await expectNoSeriousViolations(page)
    await page.getByRole('link', { name: fr.details.retake, exact: true }).click()
    await expect(page).toHaveURL(CAPTURE_URL)
  })
}

for (const [label, reply] of [
  ['coupure réseau', 'offline'],
  ['503', { status: 503, json: envelope('storage_unavailable') }],
  ['502 sans enveloppe', { status: 502, html: '<html><body>502 Bad Gateway</body></html>' }],
] as const satisfies readonly (readonly [string, Reply])[]) {
  test(`réseau / 5xx (${label}) : « Envoi impossible… », « Réessayer », saisie gardée`, async ({
    page,
    server,
  }) => {
    server.queue(reply)
    await openDetails(page)
    await option(page, fr.heapSize.large).click()
    await option(page, fr.wasteType.glass).click()
    await comment(page).fill('Derrière le stade')
    await sendButton(page).click()

    const message = page.getByText(fr.details.networkError)
    await expect(message).toBeVisible()
    await expect(message).toBeFocused()
    await expect(radio(page, fr.heapSize.large)).toBeChecked()
    await expect(radio(page, fr.wasteType.glass)).toBeChecked()
    await expect(comment(page)).toHaveValue('Derrière le stade')
    expect(await readDraft(page)).not.toBeNull()
    await expectNoSeriousViolations(page)
    await expectMobileLayout(page)

    await page.getByRole('button', { name: fr.details.retry }).click()
    await expectConfirmation(page)
    const sent = await sentReports(page)
    expect(sent).toHaveLength(2)
    expect(sentMeta(sent[1]).client_uuid).toBe(sentMeta(sent[0]).client_uuid)
  })
}

test('autre refus (409 client_uuid_conflict) : son message, brouillon gardé', async ({
  page,
  server,
}) => {
  server.queue({ status: 409, json: envelope('client_uuid_conflict') })
  await openDetails(page)
  await option(page, fr.heapSize.medium).click()
  await sendButton(page).click()
  await expect(page.getByText(fr.errors.client_uuid_conflict)).toBeVisible()
  expect(await readDraft(page)).not.toBeNull()
  await expectNoSeriousViolations(page)
})

test('consentement retiré : training false dans Dexie → consent.training = false envoyé', async ({
  page,
}) => {
  await openDetails(page, { training: true })
  await patchMeta(page, 'consent', { set: { training: false } })
  await option(page, fr.heapSize.medium).click()
  await sendButton(page).click()
  await expectConfirmation(page)
  const [sent] = await sentReports(page)
  expect(sentMeta(sent).consent).toEqual({ terms: true, training: false })
})

test('réentraînement accepté : consent.training = true envoyé', async ({ page }) => {
  await openDetails(page, { training: true })
  await option(page, fr.heapSize.medium).click()
  await sendButton(page).click()
  await expectConfirmation(page)
  const [sent] = await sentReports(page)
  expect(sentMeta(sent).consent).toEqual({ terms: true, training: true })
})

test('lien direct vers l’écran 4, sans état : accueil', async ({ page }) => {
  await page.goto('/signaler/confirmation')
  await expect(page).toHaveURL(HOME_URL)
  await expect(page.getByRole('heading', { level: 1, name: fr.app.name })).toBeVisible()
})

test('brouillon ancien, sans clientUuid : complété à la lecture, puis stable', async ({ page }) => {
  await openDetails(page)
  await patchMeta(page, 'draft', { drop: ['clientUuid'] })
  expect((await readDraft(page))?.clientUuid).toBeUndefined()

  await page.reload()
  await expect(page.getByRole('heading', { level: 1, name: fr.details.title })).toBeVisible()
  const completed = (await readDraft(page))?.clientUuid
  expect(String(completed)).toMatch(UUID_V4)
  await page.reload()
  await expect(page.getByRole('heading', { level: 1, name: fr.details.title })).toBeVisible()
  expect((await readDraft(page))?.clientUuid).toBe(completed)

  await option(page, fr.heapSize.small).click()
  await sendButton(page).click()
  await expectConfirmation(page)
  const [sent] = await sentReports(page)
  expect(sentMeta(sent).client_uuid).toBe(completed)
})
