// Brouillon du signalement (stories 1.9 et 1.13) : validation de forme à la lecture,
// aller-retour dans `meta.draft` (IndexedDB simulée) et Identifiant client (UUID v4).
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
  UUID_V4_PATTERN,
  type Draft,
  type NewDraft,
} from './draft.ts'

const BYTES = new Uint8Array([0xff, 0xd8, 0xff, 0xd9, 1, 2, 3])
const CAPTURED_AT = '2026-11-25T10:00:00.000Z'
const CAPTURED_MS = Date.parse(CAPTURED_AT)
const CLIENT_UUID = '0b8f3c52-7a4e-4f1d-9c3b-2e6a1d5f8a90'

function draft(overrides: Partial<Record<keyof Draft, unknown>> = {}): Record<string, unknown> {
  return {
    photo: new Blob([BYTES], { type: 'image/jpeg' }),
    lat: 14.6708,
    lng: -17.4381,
    accuracy: 12,
    capturedAt: CAPTURED_AT,
    clientUuid: CLIENT_UUID,
    ...overrides,
  }
}

/** Brouillon tel que la capture le remet, sans Identifiant client. */
function newDraft(overrides: Partial<Record<keyof Draft, unknown>> = {}): NewDraft {
  const { clientUuid: _ignored, ...rest } = draft(overrides)
  return rest as unknown as NewDraft
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

  it('accepte un Identifiant client en majuscules', () => {
    expect(parseDraft(draft({ clientUuid: CLIENT_UUID.toUpperCase() }))).toBeDefined()
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
    ['Identifiant client absent', draft({ clientUuid: undefined })],
    ['Identifiant client version 1', draft({ clientUuid: '6fa459ea-ee8a-11ce-9e6b-00aa006b4e5a' })],
    ['Identifiant client mal formé', draft({ clientUuid: 'pas-un-uuid' })],
    ['Identifiant client en nombre', draft({ clientUuid: 42 })],
  ])('refuse un brouillon invalide (%s)', (_, value) => {
    expect(parseDraft(value)).toBeUndefined()
  })
})

describe('meta.draft', () => {
  it('sans brouillon : undefined', async () => {
    expect(await getDraft(CAPTURED_MS)).toBeUndefined()
  })

  it('saveDraft puis getDraft : mêmes champs, mêmes octets, Identifiant client v4', async () => {
    const value = newDraft()
    const saved = await saveDraft(value)
    expect(saved.clientUuid).toMatch(UUID_V4_PATTERN)
    const read = await getDraft(CAPTURED_MS + 60_000)
    expect(read).toMatchObject({
      lat: value.lat,
      lng: value.lng,
      accuracy: value.accuracy,
      capturedAt: value.capturedAt,
      clientUuid: saved.clientUuid,
    })
    expect(read?.photo.type).toBe('image/jpeg')
    expect([...new Uint8Array(await (read as Draft).photo.arrayBuffer())]).toEqual([...BYTES])
  })

  it('l’Identifiant client reste le même à chaque lecture (renvoi, rechargement)', async () => {
    const { clientUuid } = await saveDraft(newDraft())
    for (let i = 0; i < 3; i += 1) {
      expect((await getDraft(CAPTURED_MS))?.clientUuid).toBe(clientUuid)
    }
  })

  it('chaque nouveau brouillon reçoit un nouvel Identifiant client', async () => {
    const first = await saveDraft(newDraft())
    // Un Identifiant client fourni par l'appelant est ignoré : nouveau brouillon, nouvel envoi.
    const second = await saveDraft({ ...newDraft(), clientUuid: first.clientUuid } as NewDraft)
    expect(second.clientUuid).toMatch(UUID_V4_PATTERN)
    expect(second.clientUuid).not.toBe(first.clientUuid)
    expect((await getDraft(CAPTURED_MS))?.clientUuid).toBe(second.clientUuid)
  })

  it('brouillon d’avant la story 1.13, sans Identifiant client : complété à la lecture, puis stable', async () => {
    const { clientUuid: _ignored, ...old } = draft()
    await db.meta.put({ key: 'draft', value: old })
    const first = await getDraft(CAPTURED_MS)
    expect(first?.clientUuid).toMatch(UUID_V4_PATTERN)
    const stored = (await db.meta.get('draft'))?.value as Record<string, unknown>
    expect(stored.clientUuid).toBe(first?.clientUuid)
    expect((await getDraft(CAPTURED_MS))?.clientUuid).toBe(first?.clientUuid)
  })

  it('brouillon ancien et invalide : undefined, non modifié', async () => {
    const { clientUuid: _ignored, ...old } = draft({ lat: 'ici' })
    await db.meta.put({ key: 'draft', value: old })
    expect(await getDraft(CAPTURED_MS)).toBeUndefined()
    expect((await db.meta.get('draft'))?.value).not.toHaveProperty('clientUuid')
  })

  it('Identifiant client invalide gardé : undefined, jamais remplacé', async () => {
    await db.meta.put({ key: 'draft', value: draft({ clientUuid: 'pas-un-uuid' }) })
    expect(await getDraft(CAPTURED_MS)).toBeUndefined()
    expect((await db.meta.get('draft'))?.value).toMatchObject({ clientUuid: 'pas-un-uuid' })
  })

  it('valeur gardée invalide : undefined', async () => {
    await db.meta.put({ key: 'draft', value: { ...draft(), lat: 'ici' } })
    expect(await getDraft(CAPTURED_MS)).toBeUndefined()
  })

  it('24 h exactement après la prise : gardé ; au-delà : effacé', async () => {
    await saveDraft(newDraft())
    expect(await getDraft(CAPTURED_MS + MAX_DRAFT_AGE_MS)).toBeDefined()
    expect(await getDraft(CAPTURED_MS + MAX_DRAFT_AGE_MS + 1)).toBeUndefined()
    expect(await db.meta.get('draft')).toBeUndefined()
  })

  it('prise dans le futur : gardé jusqu’à 10 minutes, effacé au-delà', async () => {
    await saveDraft(newDraft())
    expect(await getDraft(CAPTURED_MS - MAX_DRAFT_FUTURE_MS)).toBeDefined()
    expect(await getDraft(CAPTURED_MS - MAX_DRAFT_FUTURE_MS - 1)).toBeUndefined()
    expect(await db.meta.get('draft')).toBeUndefined()
  })

  it('saveDraft refuse un brouillon invalide sans rien écrire', async () => {
    await expect(saveDraft(newDraft({ accuracy: -5 }))).rejects.toThrow(TypeError)
    expect(await db.meta.get('draft')).toBeUndefined()
  })

  it('clearDraft efface le brouillon, et ne lève rien s’il est déjà vide', async () => {
    await saveDraft(newDraft())
    await clearDraft()
    expect(await getDraft(CAPTURED_MS)).toBeUndefined()
    expect(await db.meta.get('draft')).toBeUndefined()
    await expect(clearDraft()).resolves.toBeUndefined()
  })
})
