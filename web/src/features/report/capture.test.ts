// Décision de l'écran 2 · Capture : chaque ligne de la matrice de la story 1.8 et les
// seuils de précision (50 m exactement : pas d'invitation).
import { describe, expect, it } from 'vitest'

import type { PublicConfig } from '../../api/config.ts'
import {
  assessCapture,
  canTakePhoto,
  displayedAccuracy,
  isImprecise,
  keepsContinuation,
  type ConfigState,
} from './capture.ts'
import { afterPositionError, MAX_FIX_AGE_MS, type PositionState } from './usePosition.ts'

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
const READY: ConfigState = { status: 'ready', config: CONFIG }
const PLATEAU = { lat: 14.6708, lng: -17.4381 }
const THIES = { lat: 14.791, lng: -16.9359 }

function at(point: { lat: number; lng: number }, accuracy: number): PositionState {
  return { status: 'located', ...point, accuracy, fixedAt: 0 }
}

describe('seuil de précision', () => {
  it('50 m exactement : pas d’invitation ; au-delà : invitation', () => {
    expect(isImprecise(12, 50)).toBe(false)
    expect(isImprecise(50, 50)).toBe(false)
    expect(isImprecise(50.01, 50)).toBe(true)
    expect(isImprecise(80, 50)).toBe(true)
    expect(isImprecise(Number.NaN, 50)).toBe(true)
  })

  it('précision affichée arrondie vers le haut', () => {
    expect(displayedAccuracy(12)).toBe(12)
    expect(displayedAccuracy(12.2)).toBe(13)
    expect(displayedAccuracy(50)).toBe(50)
    expect(displayedAccuracy(50.2)).toBe(51)
    expect(displayedAccuracy(0.3)).toBe(1)
  })
})

describe('assessCapture', () => {
  it('position bonne (± 12 m) dans la Zone : photo permise', () => {
    const verdict = assessCapture(at(PLATEAU, 12), READY, false)
    expect(verdict).toEqual({ kind: 'ready', accuracyM: 12, imprecise: false })
    expect(canTakePhoto(verdict)).toBe(true)
  })

  it('imprécise (± 80 m) : invitation, photo en attente, puis permise après « Continuer »', () => {
    const waiting = assessCapture(at(PLATEAU, 80), READY, false)
    expect(waiting).toEqual({ kind: 'imprecise', accuracyM: 80 })
    expect(canTakePhoto(waiting)).toBe(false)
    const continued = assessCapture(at(PLATEAU, 80), READY, true)
    expect(continued).toEqual({ kind: 'ready', accuracyM: 80, imprecise: true })
    expect(canTakePhoto(continued)).toBe(true)
  })

  it('imprécise puis ≤ 50 m : photo permise sans « Continuer »', () => {
    expect(canTakePhoto(assessCapture(at(PLATEAU, 80), READY, false))).toBe(false)
    expect(canTakePhoto(assessCapture(at(PLATEAU, 30), READY, false))).toBe(true)
  })

  it('exactement 50 m : pas d’invitation', () => {
    expect(assessCapture(at(PLATEAU, 50), READY, false)).toEqual({
      kind: 'ready',
      accuracyM: 50,
      imprecise: false,
    })
  })

  it('le seuil vient de la configuration', () => {
    const strict: ConfigState = { status: 'ready', config: { ...CONFIG, report_accuracy_flag_m: 20 } }
    expect(assessCapture(at(PLATEAU, 30), strict, false).kind).toBe('imprecise')
  })

  it('hors Zone (Thiès) : photo refusée, même précise ou après « Continuer »', () => {
    expect(assessCapture(at(THIES, 5), READY, false)).toEqual({ kind: 'outside-zone' })
    expect(canTakePhoto(assessCapture(at(THIES, 80), READY, true))).toBe(false)
  })

  it('refus ou position indisponible : explication, photo refusée', () => {
    for (const reason of ['denied', 'unavailable'] as const) {
      const verdict = assessCapture({ status: 'error', reason }, READY, true)
      expect(verdict).toEqual({ kind: 'position-error', reason })
      expect(canTakePhoto(verdict)).toBe(false)
    }
  })

  it('première fois hors ligne : configuration indisponible, photo refusée', () => {
    const verdict = assessCapture(at(PLATEAU, 12), { status: 'unavailable' }, false)
    expect(verdict).toEqual({ kind: 'config-unavailable' })
    expect(canTakePhoto(verdict)).toBe(false)
  })

  it('en attente de la position ou de la configuration : photo refusée', () => {
    expect(assessCapture({ status: 'locating' }, READY, false)).toEqual({ kind: 'waiting' })
    expect(assessCapture(at(PLATEAU, 12), { status: 'loading' }, false)).toEqual({ kind: 'waiting' })
    expect(canTakePhoto({ kind: 'waiting' })).toBe(false)
  })
})

describe('« Continuer quand même » oublié hors Zone et après une erreur', () => {
  it('hors Zone ou erreur de Position : oublié ; sinon : gardé', () => {
    expect(keepsContinuation(assessCapture(at(THIES, 80), READY, true))).toBe(false)
    expect(keepsContinuation({ kind: 'position-error', reason: 'unavailable' })).toBe(false)
    expect(keepsContinuation(assessCapture(at(PLATEAU, 80), READY, true))).toBe(true)
    expect(keepsContinuation({ kind: 'waiting' })).toBe(true)
  })

  it('parcours : continuer, sortir de la Zone, revenir imprécis → nouvelle invitation', () => {
    let continued = true
    expect(assessCapture(at(PLATEAU, 80), READY, continued).kind).toBe('ready')
    const outside = assessCapture(at(THIES, 80), READY, continued)
    if (!keepsContinuation(outside)) continued = false
    expect(assessCapture(at(PLATEAU, 80), READY, continued).kind).toBe('imprecise')
  })
})

describe('afterPositionError', () => {
  const fix: PositionState = { status: 'located', ...PLATEAU, accuracy: 12, fixedAt: 1_000 }

  it('mesure manquée : la Position récente est gardée', () => {
    expect(afterPositionError(fix, 2, 1_000 + MAX_FIX_AGE_MS - 1)).toBe(fix)
    expect(afterPositionError(fix, 3, 1_000 + 5_000)).toBe(fix)
  })

  it('mesure manquée : une Position de 60 s ou plus est oubliée', () => {
    expect(afterPositionError(fix, 2, 1_000 + MAX_FIX_AGE_MS)).toEqual({
      status: 'error',
      reason: 'unavailable',
    })
  })

  it('refus : la Position est toujours oubliée', () => {
    expect(afterPositionError(fix, 1, 1_000)).toEqual({ status: 'error', reason: 'denied' })
  })

  it('sans Position : erreur', () => {
    expect(afterPositionError({ status: 'locating' }, 3, 0)).toEqual({
      status: 'error',
      reason: 'unavailable',
    })
  })
})
