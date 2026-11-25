// Consentement mémorisé dans meta (IndexedDB simulée).
import 'fake-indexeddb/auto'

import { createHash } from 'node:crypto'

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { db } from '../../offline/db.ts'
import fr from '../../i18n/fr.json'
import {
  acceptConsent,
  CONSENT_TEXT_SHA256,
  CONSENT_VERSION,
  getConsent,
  hasCurrentConsent,
} from './consent.ts'

/** Lignes `clé=valeur` de tous les textes sous `prefix`, triées. */
function textLines(value: unknown, prefix: string): string[] {
  if (value !== null && typeof value === 'object') {
    return Object.entries(value).flatMap(([key, child]) => textLines(child, `${prefix}.${key}`))
  }
  return [`${prefix}=${String(value)}`]
}

beforeEach(async () => {
  await db.meta.clear()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('consentement', () => {
  it('version datée AAAA-MM-JJ', () => {
    expect(CONSENT_VERSION).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })

  it('le texte du consentement correspond à sa version', () => {
    const digest = createHash('sha256')
      .update(textLines(fr.consent, 'consent').sort().join('\n'))
      .digest('hex')
    expect(
      digest,
      'texte du consentement modifié : changer CONSENT_VERSION et le hachage',
    ).toBe(CONSENT_TEXT_SHA256)
  })

  it('aucun consentement au premier lancement', async () => {
    expect(await getConsent()).toBeUndefined()
    expect(await hasCurrentConsent()).toBe(false)
  })

  it('acceptation sans la case : training = false, date ISO de l’appareil', async () => {
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(new Date('2026-11-25T09:30:00.000Z'))
    const consent = await acceptConsent({ training: false })
    const expected = {
      acceptedAt: '2026-11-25T09:30:00.000Z',
      version: CONSENT_VERSION,
      training: false,
    }
    expect(consent).toEqual(expected)
    expect(await db.meta.get('consent')).toEqual({ key: 'consent', value: expected })
    expect(await hasCurrentConsent()).toBe(true)
  })

  it('acceptation avec la case : training = true', async () => {
    await acceptConsent({ training: true })
    const consent = await getConsent()
    expect(consent?.training).toBe(true)
    expect(consent?.version).toBe(CONSENT_VERSION)
    expect(Number.isNaN(Date.parse(consent?.acceptedAt ?? ''))).toBe(false)
  })

  it('une nouvelle acceptation remplace la précédente', async () => {
    await acceptConsent({ training: true })
    await acceptConsent({ training: false })
    expect((await getConsent())?.training).toBe(false)
  })

  it('version périmée : le consentement est redemandé', async () => {
    await db.meta.put({
      key: 'consent',
      value: { acceptedAt: '2026-01-01T00:00:00.000Z', version: '2026-01-01', training: true },
    })
    expect((await getConsent())?.version).toBe('2026-01-01')
    expect(await hasCurrentConsent()).toBe(false)
  })

  it('date d’acceptation illisible : le consentement est redemandé', async () => {
    await db.meta.put({
      key: 'consent',
      value: { acceptedAt: 'pas une date', version: CONSENT_VERSION, training: false },
    })
    expect(await hasCurrentConsent()).toBe(false)
  })

  it('valeur illisible : traitée comme absente', async () => {
    await db.meta.put({ key: 'consent', value: { version: CONSENT_VERSION } })
    expect(await getConsent()).toBeUndefined()
    expect(await hasCurrentConsent()).toBe(false)
  })
})
