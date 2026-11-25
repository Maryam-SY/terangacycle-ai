// Brouillon du signalement en cours (story 1.9), gardé sur l'appareil dans Dexie
// (`meta.draft`) : la photo traitée (les octets exacts qui seront envoyés), la Position,
// sa précision et l'heure de la prise. Lu par l'écran 3 ; aucune requête ici.
// Donnée personnelle (photo et Position exacte) : rien n'est écrit dans la console, et un
// brouillon périmé est effacé dès sa lecture.
import { MAX_PHOTO_AGE_MS, MAX_PHOTO_BYTES } from '../features/report/photo.ts'
import { deleteMeta, getMeta, setMeta } from './db.ts'

/** Durée de vie d'un brouillon, comptée depuis la prise. */
export const MAX_DRAFT_AGE_MS = 24 * 3600_000
/** Écart toléré pour une prise datée dans le futur (horloge de l'appareil corrigée). */
export const MAX_DRAFT_FUTURE_MS = MAX_PHOTO_AGE_MS

export interface Draft {
  /** JPEG produit par `processPhoto`, sans métadonnées. */
  photo: Blob
  lat: number
  lng: number
  /** Précision de la Position, en mètres. */
  accuracy: number
  /** Heure de l'appareil au moment de la prise, ISO 8601. */
  capturedAt: string
}

function isNumberIn(value: unknown, min: number, max: number): value is number {
  return typeof value === 'number' && Number.isFinite(value) && value >= min && value <= max
}

/** Brouillon validé, ou `undefined` si la valeur n'a pas la forme attendue. */
export function parseDraft(value: unknown): Draft | undefined {
  if (value === null || typeof value !== 'object') return undefined
  const { photo, lat, lng, accuracy, capturedAt } = value as Record<string, unknown>
  if (!(photo instanceof Blob) || photo.type !== 'image/jpeg') return undefined
  if (photo.size === 0 || photo.size > MAX_PHOTO_BYTES) return undefined
  if (!isNumberIn(lat, -90, 90) || !isNumberIn(lng, -180, 180)) return undefined
  if (!isNumberIn(accuracy, 0, Number.MAX_VALUE)) return undefined
  if (typeof capturedAt !== 'string' || Number.isNaN(Date.parse(capturedAt))) return undefined
  return { photo, lat, lng, accuracy, capturedAt }
}

/** Garde le brouillon tel quel (le Blob est stocké sans copie ni ré-encodage). */
export async function saveDraft(draft: Draft): Promise<void> {
  const valid = parseDraft(draft)
  if (!valid) throw new TypeError('brouillon invalide')
  await setMeta('draft', valid)
}

/** Vrai si la prise date de plus de `MAX_DRAFT_AGE_MS`, ou de plus de
 *  `MAX_DRAFT_FUTURE_MS` dans le futur. */
export function isDraftExpired(draft: Draft, now: number): boolean {
  const age = now - Date.parse(draft.capturedAt)
  return age > MAX_DRAFT_AGE_MS || age < -MAX_DRAFT_FUTURE_MS
}

/** Brouillon gardé, valide et non périmé ; `undefined` s'il manque, n'a pas la forme
 *  attendue ou est périmé (il est alors effacé). */
export async function getDraft(now: number = Date.now()): Promise<Draft | undefined> {
  const draft = parseDraft(await getMeta('draft'))
  if (draft && isDraftExpired(draft, now)) {
    await clearDraft()
    return undefined
  }
  return draft
}

export async function clearDraft(): Promise<void> {
  await deleteMeta('draft')
}
