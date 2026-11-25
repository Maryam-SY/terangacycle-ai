// Brouillon du signalement (story 1.9) : validation de forme à la lecture, et aller-retour
// dans `meta.draft` (IndexedDB simulée).
import 'fake-indexeddb/auto'

import { beforeEach, describe, expect, it } from 'vitest'

import { MAX_PHOTO_BYTES } from '../features/report/photo.ts'
import { db } from './db.ts'
import {
  clearDraft,
  getDraft,
  MAX_DRAFT_AGE_MS,
  MAX_DRAFT_FUTURE_MS,
  parseDraft,
  saveDraft,
  type Draft,
} from './draft.ts'

const BYTES = new Uint8Array([0xff, 0xd8, 0xff, 0xd9, 1, 2, 3])
const CAPTURED_AT = '2026-11-25T10:00:00.000Z'
const CAPTURED_MS = Date.parse(CAPTURED_AT)

function draft(overrides: Partial<Record<keyof Draft, unknown>> = {}): Record<string, unknown> {
  return {
    photo: new Blob([BYTES], { type: 'image/jpeg' }),
    lat: 14.6708,
    lng: -17.4381,
    accuracy: 12,
    capturedAt: CAPTURED_AT,
    ...overrides,
  }
}

beforeEach(async () => {
  await db.meta.clear()
})

describe('parseDraft', () => {
  it('accepte un brouillon complet', () => {
    const value = draft()
    expect(parseDraft(value)).toEqual(value)
  })

  it('ignore les champs en trop', () => {
    expect(parseDraft({ ...draft(), extra: 1 })).not.toHaveProperty('extra')
  })

  it.each([
    ['null', null],
    ['texte', 'brouillon'],
    ['photo absente', draft({ photo: undefined })],
    ['photo en octets bruts', draft({ photo: BYTES })],
    ['photo PNG', draft({ photo: new Blob([BYTES], { type: 'image/png' }) })],
    ['photo vide', draft({ photo: new Blob([], { type: 'image/jpeg' }) })],
    [
      'photo trop lourde',
      draft({ photo: new Blob([new Uint8Array(MAX_PHOTO_BYTES + 1)], { type: 'image/jpeg' }) }),
    ],
    ['latitude hors bornes', draft({ lat: 91 })],
    ['longitude hors bornes', draft({ lng: -181 })],
    ['latitude en texte', draft({ lat: '14.67' })],
    ['latitude NaN', draft({ lat: Number.NaN })],
    ['précision négative', draft({ accuracy: -1 })],
    ['précision infinie', draft({ accuracy: Number.POSITIVE_INFINITY })],
    ['précision absente', draft({ accuracy: undefined })],
    ['date illisible', draft({ capturedAt: 'hier' })],
    ['date en nombre', draft({ capturedAt: 1_764_064_800_000 })],
  ])('refuse un brouillon invalide (%s)', (_, value) => {
    expect(parseDraft(value)).toBeUndefined()
  })
})

describe('meta.draft', () => {
  it('sans brouillon : undefined', async () => {
    expect(await getDraft(CAPTURED_MS)).toBeUndefined()
  })

  it('saveDraft puis getDraft : mêmes champs, mêmes octets', async () => {
    const value = draft() as unknown as Draft
    await saveDraft(value)
    const read = await getDraft(CAPTURED_MS + 60_000)
    expect(read).toMatchObject({
      lat: value.lat,
      lng: value.lng,
      accuracy: value.accuracy,
      capturedAt: value.capturedAt,
    })
    expect(read?.photo.type).toBe('image/jpeg')
    expect([...new Uint8Array(await (read as Draft).photo.arrayBuffer())]).toEqual([...BYTES])
  })

  it('valeur gardée invalide : undefined', async () => {
    await db.meta.put({ key: 'draft', value: { ...draft(), lat: 'ici' } })
    expect(await getDraft(CAPTURED_MS)).toBeUndefined()
  })

  it('24 h exactement après la prise : gardé ; au-delà : effacé', async () => {
    await saveDraft(draft() as unknown as Draft)
    expect(await getDraft(CAPTURED_MS + MAX_DRAFT_AGE_MS)).toBeDefined()
    expect(await getDraft(CAPTURED_MS + MAX_DRAFT_AGE_MS + 1)).toBeUndefined()
    expect(await db.meta.get('draft')).toBeUndefined()
  })

  it('prise dans le futur : gardé jusqu’à 10 minutes, effacé au-delà', async () => {
    await saveDraft(draft() as unknown as Draft)
    expect(await getDraft(CAPTURED_MS - MAX_DRAFT_FUTURE_MS)).toBeDefined()
    expect(await getDraft(CAPTURED_MS - MAX_DRAFT_FUTURE_MS - 1)).toBeUndefined()
    expect(await db.meta.get('draft')).toBeUndefined()
  })

  it('saveDraft refuse un brouillon invalide sans rien écrire', async () => {
    await expect(saveDraft(draft({ accuracy: -5 }) as unknown as Draft)).rejects.toThrow(TypeError)
    expect(await db.meta.get('draft')).toBeUndefined()
  })

  it('clearDraft efface le brouillon', async () => {
    await saveDraft(draft() as unknown as Draft)
    await clearDraft()
    expect(await getDraft(CAPTURED_MS)).toBeUndefined()
    expect(await db.meta.get('draft')).toBeUndefined()
  })
})
