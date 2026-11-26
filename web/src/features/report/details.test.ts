// Règles de l'écran 3 (story 1.13) : raison d'un envoi impossible, commentaire en points
// de code, `meta` envoyé, conduite à tenir pour chaque erreur.
import { describe, expect, it } from 'vitest'

import { ApiError, NetworkError } from '../../api/client.ts'
import { toggleWasteType } from '../classify/wasteTypes.ts'
import type { Draft } from '../../offline/draft.ts'
import {
  buildMeta,
  codePointLength,
  COMMENT_MAX,
  limitComment,
  missingField,
  sendFailure,
} from './details.ts'

const DRAFT: Draft = {
  photo: new Blob([new Uint8Array([0xff, 0xd8, 0xff, 0xd9])], { type: 'image/jpeg' }),
  lat: 14.6708,
  lng: -17.4381,
  accuracy: 9,
  capturedAt: '2026-11-26T10:00:00.000Z',
  clientUuid: '0b8f3c52-7a4e-4f1d-9c3b-2e6a1d5f8a90',
}
const EMOJI = '🙏'

describe('missingField : « Envoyer » désactivé tant qu’il manque…', () => {
  it('la photo', () => {
    expect(missingField(undefined, 'small')).toBe('photo')
    expect(missingField({ ...DRAFT, photo: new Blob([]) }, 'small')).toBe('photo')
  })

  it('la Position', () => {
    expect(missingField({ ...DRAFT, lat: Number.NaN }, 'small')).toBe('position')
    expect(missingField({ ...DRAFT, accuracy: Number.POSITIVE_INFINITY }, 'small')).toBe('position')
  })

  it('la Taille de tas', () => {
    expect(missingField(DRAFT, undefined)).toBe('heapSize')
  })

  it('rien : envoi possible, Type et commentaire facultatifs', () => {
    expect(missingField(DRAFT, 'medium')).toBeUndefined()
  })
})

describe('commentaire : 280 points de code', () => {
  it('compte un emoji pour un caractère', () => {
    expect(EMOJI.length).toBe(2)
    expect(codePointLength(EMOJI.repeat(3))).toBe(3)
    expect(codePointLength('')).toBe(0)
  })

  it('280 emojis acceptés ; la 281e frappe est ignorée', () => {
    const full = EMOJI.repeat(COMMENT_MAX)
    expect(limitComment(EMOJI.repeat(COMMENT_MAX - 1), full)).toBe(full)
    expect(codePointLength(full)).toBe(280)
    expect(limitComment(full, `${full}a`)).toBe(full)
    // Frappe au milieu du texte : ignorée aussi, le texte reste tel quel.
    expect(limitComment(full, `a${full}`)).toBe(full)
  })

  it('un collage trop long est tronqué à 280 points de code, sans couper un emoji', () => {
    const pasted = EMOJI.repeat(300)
    const kept = limitComment('', pasted)
    expect(codePointLength(kept)).toBe(280)
    expect(kept).toBe(EMOJI.repeat(280))
  })

  it('sous la limite, ou en effaçant : la saisie passe telle quelle', () => {
    expect(limitComment('', 'Près de l’école')).toBe('Près de l’école')
    const full = 'x'.repeat(COMMENT_MAX)
    expect(limitComment(full, full.slice(1))).toBe(full.slice(1))
  })
})

describe('Type de déchet facultatif', () => {
  it('toucher le Type choisi le retire ; un autre le remplace', () => {
    expect(toggleWasteType(undefined, 'plastic')).toBe('plastic')
    expect(toggleWasteType('plastic', 'plastic')).toBeUndefined()
    expect(toggleWasteType('plastic', 'glass')).toBe('glass')
  })
})

describe('buildMeta', () => {
  const consent = { terms: true, training: false }

  it('nominal : Taille seule, sans Type ni commentaire', () => {
    expect(buildMeta(DRAFT, { heapSize: 'medium', comment: '' }, consent)).toEqual({
      client_uuid: DRAFT.clientUuid,
      lat: DRAFT.lat,
      lng: DRAFT.lng,
      accuracy_m: DRAFT.accuracy,
      captured_at: DRAFT.capturedAt,
      heap_size: 'medium',
      consent: { terms: true, training: false },
    })
  })

  it('complet : Type et commentaire envoyés', () => {
    const comment = EMOJI.repeat(COMMENT_MAX)
    const meta = buildMeta(DRAFT, { heapSize: 'large', wasteType: 'plastic', comment }, consent)
    expect(meta).toMatchObject({ heap_size: 'large', waste_type: 'plastic', comment })
  })

  it('commentaire blanc : absent ; blancs de bord retirés', () => {
    expect(buildMeta(DRAFT, { heapSize: 'small', comment: '   \n' }, consent)).not.toHaveProperty(
      'comment',
    )
    expect(buildMeta(DRAFT, { heapSize: 'small', comment: '  ici  ' }, consent).comment).toBe('ici')
  })

  it('Type retiré : waste_type absent', () => {
    const meta = buildMeta(DRAFT, { heapSize: 'small', wasteType: undefined, comment: '' }, consent)
    expect(meta).not.toHaveProperty('waste_type')
  })

  it('consentement lu au moment de l’envoi, réentraînement compris', () => {
    expect(
      buildMeta(DRAFT, { heapSize: 'small', comment: '' }, { terms: true, training: true }).consent,
    ).toEqual({ terms: true, training: true })
    expect(
      buildMeta(DRAFT, { heapSize: 'small', comment: '' }, { terms: false, training: false })
        .consent,
    ).toEqual({ terms: false, training: false })
  })
})

describe('sendFailure : conduite à tenir par erreur', () => {
  const retry = { kind: 'retry', messageKey: 'details.networkError' }

  it.each([
    ['coupure réseau', new NetworkError()],
    ['erreur imprévue', new Error('x')],
    ['503 storage_unavailable', new ApiError(503, 'storage_unavailable')],
    ['500 internal_error', new ApiError(500, 'internal_error')],
    ['502 sans enveloppe', new ApiError(502, undefined)],
  ])('%s : « Envoi impossible… », réessayer', (_, error) => {
    expect(sendFailure(error)).toEqual(retry)
  })

  it('422 outside_active_zone : message et retour à l’écran 2', () => {
    expect(sendFailure(new ApiError(422, 'outside_active_zone'))).toEqual({
      kind: 'outside-zone',
      messageKey: 'errors.outside_active_zone',
    })
  })

  it('422 consent_required : écran de consentement', () => {
    expect(sendFailure(new ApiError(422, 'consent_required'))).toEqual({ kind: 'consent' })
  })

  it.each([
    [413, 'photo_too_large'],
    [415, 'unsupported_media_type'],
    [422, 'photo_unreadable'],
    [422, 'photo_too_many_pixels'],
  ])('%i %s : reprendre la photo', (status, code) => {
    expect(sendFailure(new ApiError(status, code))).toEqual({
      kind: 'retake',
      messageKey: `errors.${code}`,
    })
  })

  it.each([
    [400, 'invalid_device_id'],
    [409, 'client_uuid_conflict'],
    [422, 'validation_error'],
    [401, 'invalid_token'],
  ])('%i %s : son message, brouillon gardé', (status, code) => {
    expect(sendFailure(new ApiError(status, code))).toEqual({
      kind: 'message',
      messageKey: `errors.${code}`,
    })
  })

  it('code inconnu (429) : message générique', () => {
    expect(sendFailure(new ApiError(429, 'rate_limited'))).toEqual({
      kind: 'message',
      messageKey: 'errors.internal_error',
    })
  })
})
