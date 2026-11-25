// Story 1.7 : accueil, Identifiant d'appareil et consentement avant la première capture.
// Une ligne de la matrice I/O de la spec par test, en 390×844 sur la PWA construite.
// Espions posés avant tout script de la page : géolocalisation, appareil photo, réseau.
import { readFileSync } from 'node:fs'

import AxeBuilder from '@axe-core/playwright'
import { test as base, expect, type Page } from '@playwright/test'

declare global {
  interface Window {
    __permissionCalls?: string[]
  }
}

interface Texts {
  app: { name: string }
  home: { report: string }
  consent: {
    title: string
    accept: string
    decline: string
    saveError: string
    training: { label: string }
  }
  capture: { title: string }
}

const fr = JSON.parse(
  readFileSync(new URL('../src/i18n/fr.json', import.meta.url), 'utf8'),
) as Texts

const DB_NAME = 'terangacycle'
const DEVICE_ID = /^[A-Za-z0-9_-]{43}$/
const CONSENT_URL = /\/signaler\/consentement$/
const CAPTURE_URL = /\/signaler\/capture$/
const HOME_URL = /:\d+\/$/

interface Watch {
  /** URL de toutes les requêtes du contexte (page et workers). */
  requests: string[]
  /** Textes des messages de console de la page. */
  consoleMessages: string[]
  /** Appels aux API de géolocalisation et d'appareil photo depuis le dernier chargement. */
  permissionCalls: () => Promise<string[]>
}

const test = base.extend<{ watch: Watch }>({
  // Second argument nommé `provide` (et non `use`) : la règle rules-of-hooks le prendrait pour un hook.
  watch: async ({ page, context }, provide) => {
    await page.addInitScript(() => {
      const calls: string[] = []
      Object.defineProperty(window, '__permissionCalls', { value: calls })
      const spy = (target: object | undefined, name: string, label: string) => {
        if (!target) return
        Object.defineProperty(target, name, {
          configurable: true,
          value: () => {
            calls.push(label)
            return label === 'mediaDevices.getUserMedia'
              ? Promise.reject(new DOMException('espion', 'NotAllowedError'))
              : 0
          },
        })
      }
      spy(navigator.geolocation, 'getCurrentPosition', 'geolocation.getCurrentPosition')
      spy(navigator.geolocation, 'watchPosition', 'geolocation.watchPosition')
      spy(navigator.mediaDevices, 'getUserMedia', 'mediaDevices.getUserMedia')
    })
    const requests: string[] = []
    const consoleMessages: string[] = []
    context.on('request', (request) => requests.push(request.url()))
    page.on('console', (message) => consoleMessages.push(message.text()))
    await provide({
      requests,
      consoleMessages,
      permissionCalls: () => page.evaluate(() => [...(window.__permissionCalls ?? [])]),
    })
  },
})

/** Valeur de `meta[key]`, lue sans Dexie ; `undefined` si la base n'existe pas encore. */
function readMeta(page: Page, key: string): Promise<unknown> {
  return page.evaluate(
    async ({ name, key }) => {
      const databases = await indexedDB.databases()
      if (!databases.some((database) => database.name === name)) return undefined
      return new Promise<unknown>((resolve, reject) => {
        const open = indexedDB.open(name)
        open.onerror = () => reject(open.error)
        open.onsuccess = () => {
          const database = open.result
          if (!database.objectStoreNames.contains('meta')) {
            database.close()
            resolve(undefined)
            return
          }
          const request = database.transaction('meta', 'readonly').objectStore('meta').get(key)
          request.onsuccess = () => {
            database.close()
            resolve((request.result as { value?: unknown } | undefined)?.value)
          }
          request.onerror = () => {
            database.close()
            reject(request.error)
          }
        }
      })
    },
    { name: DB_NAME, key },
  )
}

/** Écrit `meta[key]` sans Dexie (la base doit déjà exister). */
function writeMeta(page: Page, key: string, value: unknown): Promise<void> {
  return page.evaluate(
    ({ name, key, value }) =>
      new Promise<void>((resolve, reject) => {
        const open = indexedDB.open(name)
        open.onerror = () => reject(open.error)
        // Base absente : open() la créerait vide (version 1, sans `meta`).
        open.onupgradeneeded = () => {
          open.transaction?.abort()
          reject(new Error(`base ${name} absente`))
        }
        open.onsuccess = () => {
          const database = open.result
          if (!database.objectStoreNames.contains('meta')) {
            database.close()
            reject(new Error(`table meta absente de ${name}`))
            return
          }
          const transaction = database.transaction('meta', 'readwrite')
          transaction.objectStore('meta').put({ key, value })
          transaction.oncomplete = () => {
            database.close()
            resolve()
          }
          transaction.onerror = () => {
            database.close()
            reject(transaction.error)
          }
          transaction.onabort = () => {
            database.close()
            reject(transaction.error ?? new Error('transaction annulée'))
          }
        }
      }),
    { name: DB_NAME, key, value },
  )
}

/** Accueil chargé et Identifiant d'appareil créé (la base existe). */
async function openHome(page: Page): Promise<string> {
  await page.goto('/')
  await expect.poll(() => readMeta(page, 'deviceId')).toMatch(DEVICE_ID)
  return (await readMeta(page, 'deviceId')) as string
}

function reportButton(page: Page) {
  return page.getByRole('link', { name: fr.home.report })
}

async function expectConsentScreen(page: Page) {
  await expect(page).toHaveURL(CONSENT_URL)
  await expect(page.getByRole('heading', { level: 1, name: fr.consent.title })).toBeVisible()
}

async function expectCaptureScreen(page: Page) {
  await expect(page).toHaveURL(CAPTURE_URL)
  await expect(page.getByRole('heading', { level: 1, name: fr.capture.title })).toBeVisible()
}

function reportRequests(watch: Watch): string[] {
  return watch.requests.filter((url) => new URL(url).pathname.startsWith('/v1/reports'))
}

async function expectStoredConsent(page: Page, training: boolean) {
  const consent = (await readMeta(page, 'consent')) as Record<string, unknown> | undefined
  expect(consent).toEqual({
    acceptedAt: expect.any(String),
    version: expect.stringMatching(/^\d{4}-\d{2}-\d{2}$/),
    training,
  })
  const acceptedAt = consent?.acceptedAt as string
  expect(new Date(acceptedAt).toISOString()).toBe(acceptedAt)
}

test('témoin : les espions enregistrent la géolocalisation et l’appareil photo', async ({
  page,
  watch,
}) => {
  await page.goto('/')
  await page.evaluate(async () => {
    navigator.geolocation.getCurrentPosition(() => undefined)
    navigator.geolocation.watchPosition(() => undefined)
    await navigator.mediaDevices.getUserMedia({ video: true }).catch(() => undefined)
  })
  expect(await watch.permissionCalls()).toEqual([
    'geolocation.getCurrentPosition',
    'geolocation.watchPosition',
    'mediaDevices.getUserMedia',
  ])
})

test('premier lancement puis relance : un seul identifiant, jamais affiché ni journalisé', async ({
  page,
  watch,
}) => {
  const deviceId = await openHome(page)
  expect(deviceId).toMatch(DEVICE_ID)

  await page.reload()
  await expect(reportButton(page)).toBeVisible()
  expect(await readMeta(page, 'deviceId')).toBe(deviceId)

  await expect(page.locator('body')).not.toContainText(deviceId)
  expect(await page.content()).not.toContain(deviceId)
  expect(watch.consoleMessages.filter((text) => text.includes(deviceId))).toEqual([])
})

test('accueil 390×844 : « Signaler un dépôt » d’au moins 44 px, sans défilement horizontal', async ({
  page,
}) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { level: 1, name: fr.app.name })).toBeVisible()
  const button = reportButton(page)
  await expect(button).toBeVisible()
  const box = await button.boundingBox()
  expect(box?.width).toBeGreaterThanOrEqual(44)
  expect(box?.height).toBeGreaterThanOrEqual(44)
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  )
  expect(overflow).toBeLessThanOrEqual(0)
})

test('premier signalement : consentement, sans géolocalisation, appareil photo ni /v1/reports', async ({
  page,
  watch,
}) => {
  await openHome(page)
  await reportButton(page).click()
  await expectConsentScreen(page)
  // Navigation côté client : le focus suit le titre du nouvel écran (lecteurs d'écran).
  await expect(page.getByRole('heading', { level: 1, name: fr.consent.title })).toBeFocused()
  await expect(page.getByRole('checkbox', { name: fr.consent.training.label })).not.toBeChecked()
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  )
  expect(overflow).toBeLessThanOrEqual(0)

  expect(await watch.permissionCalls()).toEqual([])
  expect(reportRequests(watch)).toEqual([])
})

test('refus : retour à l’accueil, rien de mémorisé, consentement redemandé', async ({
  page,
  watch,
}) => {
  await openHome(page)
  await reportButton(page).click()
  await expectConsentScreen(page)

  await page.getByRole('button', { name: fr.consent.decline }).click()
  await expect(page).toHaveURL(HOME_URL)
  expect(await readMeta(page, 'consent')).toBeUndefined()

  await reportButton(page).click()
  await expectConsentScreen(page)
  expect(await watch.permissionCalls()).toEqual([])
  expect(reportRequests(watch)).toEqual([])
})

test('acceptation sans la case : training = false, puis écran 2', async ({ page, watch }) => {
  await openHome(page)
  await reportButton(page).click()
  await expectConsentScreen(page)

  await page.getByRole('button', { name: fr.consent.accept }).click()
  await expectCaptureScreen(page)
  await expectStoredConsent(page, false)

  expect(await watch.permissionCalls()).toEqual([])
  expect(reportRequests(watch)).toEqual([])
})

test('acceptation avec la case : training = true', async ({ page }) => {
  await openHome(page)
  await reportButton(page).click()
  await expectConsentScreen(page)

  // Le libellé coche la case : cible tactile plus grande que la case elle-même.
  await page.getByText(fr.consent.training.label).click()
  await expect(page.getByRole('checkbox', { name: fr.consent.training.label })).toBeChecked()
  await page.getByRole('button', { name: fr.consent.accept }).click()
  await expectCaptureScreen(page)
  await expectStoredConsent(page, true)
})

test('consentement à jour : « Signaler un dépôt » ouvre directement l’écran 2, même après relance', async ({
  page,
}) => {
  await openHome(page)
  await reportButton(page).click()
  await page.getByRole('button', { name: fr.consent.accept }).click()
  await expectCaptureScreen(page)

  // Relance : nouveau chargement complet de l'accueil.
  await page.goto('/')
  await reportButton(page).click()
  await expectCaptureScreen(page)
  await expect(page.getByRole('heading', { name: fr.consent.title })).toHaveCount(0)
})

test('nouvelle version du texte : le consentement est redemandé', async ({ page }) => {
  await openHome(page)
  await writeMeta(page, 'consent', {
    acceptedAt: '2026-01-01T00:00:00.000Z',
    version: '2000-01-01',
    training: true,
  })

  await reportButton(page).click()
  await expectConsentScreen(page)

  await page.goto('/signaler/capture')
  await expectConsentScreen(page)
})

test('échec de l’enregistrement : message, même écran, nouvel essai possible, rien de mémorisé', async ({
  page,
}) => {
  await openHome(page)
  await reportButton(page).click()
  await expectConsentScreen(page)

  await page.evaluate(() => {
    IDBObjectStore.prototype.put = () => {
      throw new DOMException('espace saturé (test)', 'QuotaExceededError')
    }
  })
  const accept = page.getByRole('button', { name: fr.consent.accept })
  await accept.click()

  await expect(page.getByRole('alert')).toContainText(fr.consent.saveError)
  await expect(page).toHaveURL(CONSENT_URL)
  await expect(accept).toBeEnabled()
  await expect(page.getByRole('button', { name: fr.consent.decline })).toBeEnabled()
  expect(await readMeta(page, 'consent')).toBeUndefined()
})

test('base illisible : /signaler et /signaler/capture mènent au consentement', async ({ page }) => {
  await page.addInitScript(() => {
    IDBFactory.prototype.open = () => {
      throw new DOMException('base bloquée (test)', 'UnknownError')
    }
  })

  await page.goto('/signaler')
  await expectConsentScreen(page)

  await page.goto('/signaler/capture')
  await expectConsentScreen(page)
})

test('lien direct /signaler/capture sans consentement : redirection vers le consentement', async ({
  page,
  watch,
}) => {
  await page.goto('/signaler/capture')
  await expectConsentScreen(page)
  expect(await watch.permissionCalls()).toEqual([])
  expect(reportRequests(watch)).toEqual([])
})

test.describe('accessibilité (axe) : aucune violation critical ni serious', () => {
  async function seriousViolations(page: Page) {
    const { violations } = await new AxeBuilder({ page }).analyze()
    return violations
      .filter((violation) => violation.impact === 'critical' || violation.impact === 'serious')
      .map((violation) => `${violation.id} (${violation.impact}) : ${violation.help}`)
  }

  test('accueil', async ({ page }) => {
    await page.goto('/')
    await expect(reportButton(page)).toBeVisible()
    expect(await seriousViolations(page)).toEqual([])
  })

  test('consentement', async ({ page }) => {
    await page.goto('/signaler/consentement')
    await expectConsentScreen(page)
    expect(await seriousViolations(page)).toEqual([])
  })
})
