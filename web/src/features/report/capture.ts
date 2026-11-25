// Décision de l'écran 2 · Capture (story 1.8) : la photo n'est permise que si la Position
// est utilisable, c'est-à-dire dans la Zone active et assez précise (ou acceptée telle
// quelle par « Continuer quand même »). Fonction pure, testée sans navigateur.
import type { PublicConfig } from '../../api/config.ts'
import { multiPolygonCovers } from './geo.ts'
import type { PositionState } from './usePosition.ts'

export type ConfigState =
  | { status: 'loading' }
  | { status: 'ready'; config: PublicConfig }
  | { status: 'unavailable' }

export type CaptureVerdict =
  /** Position ou configuration en cours d'obtention. */
  | { kind: 'waiting' }
  | { kind: 'position-error'; reason: 'denied' | 'unavailable' }
  /** Ni réseau ni configuration gardée : une première connexion est nécessaire. */
  | { kind: 'config-unavailable' }
  | { kind: 'outside-zone' }
  /** Précision au-delà du seuil : invitation à patienter, photo en attente. */
  | { kind: 'imprecise'; accuracyM: number }
  /** Photo permise ; `imprecise` si le Citoyen a choisi de continuer quand même. */
  | { kind: 'ready'; accuracyM: number; imprecise: boolean }

/** Précision affichée, arrondie vers le haut : « ± 51 m » n'est jamais montré comme 50. */
export function displayedAccuracy(accuracy: number): number {
  return Math.max(1, Math.ceil(accuracy))
}

/** Au-delà du seuil : invitation à patienter. Exactement le seuil : pas d'invitation. */
export function isImprecise(accuracy: number, flagM: number): boolean {
  return !(accuracy <= flagM)
}

export function assessCapture(
  position: PositionState,
  config: ConfigState,
  continuedAnyway: boolean,
): CaptureVerdict {
  if (position.status === 'error') return { kind: 'position-error', reason: position.reason }
  if (config.status === 'unavailable') return { kind: 'config-unavailable' }
  if (position.status === 'locating' || config.status === 'loading') return { kind: 'waiting' }

  const { lat, lng, accuracy } = position
  const { active_zone: zone, report_accuracy_flag_m: flagM } = config.config
  if (!multiPolygonCovers(zone.geometry, lat, lng)) return { kind: 'outside-zone' }

  const accuracyM = displayedAccuracy(accuracy)
  const imprecise = isImprecise(accuracy, flagM)
  if (imprecise && !continuedAnyway) return { kind: 'imprecise', accuracyM }
  return { kind: 'ready', accuracyM, imprecise }
}

export function canTakePhoto(verdict: CaptureVerdict): boolean {
  return verdict.kind === 'ready'
}

/** Faux quand « Continuer quand même » doit être oublié : hors Zone ou après une erreur de
 *  Position, la Position suivante est une nouvelle Position. */
export function keepsContinuation(verdict: CaptureVerdict): boolean {
  return verdict.kind !== 'outside-zone' && verdict.kind !== 'position-error'
}
