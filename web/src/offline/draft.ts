// Brouillon du signalement en cours (story 1.9), gardé sur l'appareil dans Dexie
// (`meta.draft`) : la photo traitée (les octets exacts qui seront envoyés), la Position,
// sa précision, l'heure de la prise et l'Identifiant client (story 1.13), un UUID v4 tiré
// à la création du brouillon et renvoyé tel quel à chaque nouvel essai d'envoi : le
// serveur reconnaît ainsi un renvoi (200) au lieu de créer un doublon. Lu par l'écran 3 ;
// aucune requête ici.
// Donnée personnelle (photo et Position exacte) : rien n'est écrit dans la console, et un
// brouillon périmé est effacé dès sa lecture.
import { MAX_PHOTO_AGE_MS, MAX_PHOTO_BYTES } from '../features/report/photo.ts'
import { db, deleteMeta, setMeta } from './db.ts'

/** Durée de vie d'un brouillon, comptée depuis la prise. */
export const MAX_DRAFT_AGE_MS = 24 * 3600_000
/** Écart toléré pour une prise datée dans le futur (horloge de l'appareil corrigée). */
export const MAX_DRAFT_FUTURE_MS = MAX_PHOTO_AGE_MS
/** UUID version 4 (RFC 9562), forme canonique en minuscules ou majuscules. */
export const UUID_V4_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

export interface Draft {
  /** JPEG produit par `processPhoto`, sans métadonnées. */
  photo: Blob
  lat: number
  lng: number
  /** Précision de la Position, en mètres. */
  accuracy: number
  /** Heure de l'appareil au moment de la prise, ISO 8601. */
  capturedAt: string
  /** Identifiant client (UUID v4), `meta.client_uuid` de chaque envoi de ce brouillon. */
  clientUuid: string
}

/** Brouillon tel que la capture le remet : l'Identifiant client est attribué ici. */
export type NewDraft = Omit<Draft, 'clientUuid'>

function isNumberIn(value: unknown, min: number, max: number): value is number {
  return typeof value === 'number' && Number.isFinite(value) && value >= min && value <= max
}

/** Brouillon validé, ou `undefined` si la valeur n'a pas la forme attendue. */
export function parseDraft(value: unknown): Draft | undefined {
  if (value === null || typeof value !== 'object') return undefined
  const { photo, lat, lng, accuracy, capturedAt, clientUuid } = value as Record<string, unknown>
  if (!(photo instanceof Blob) || photo.type !== 'image/jpeg') return undefined
  if (photo.size === 0 || photo.size > MAX_PHOTO_BYTES) return undefined
  if (!isNumberIn(lat, -90, 90) || !isNumberIn(lng, -180, 180)) return undefined
  if (!isNumberIn(accuracy, 0, Number.MAX_VALUE)) return undefined
  if (typeof capturedAt !== 'string' || Number.isNaN(Date.parse(capturedAt))) return undefined
  if (typeof clientUuid !== 'string' || !UUID_V4_PATTERN.test(clientUuid)) return undefined
  return { photo, lat, lng, accuracy, capturedAt, clientUuid }
}

/** Garde un nouveau brouillon (le Blob est stocké sans copie ni ré-encodage), avec un
 *  nouvel Identifiant client ; renvoie le brouillon gardé. */
export async function saveDraft(draft: NewDraft): Promise<Draft> {
  const { photo, lat, lng, accuracy, capturedAt } = draft
  const valid = parseDraft({ photo, lat, lng, accuracy, capturedAt, clientUuid: crypto.randomUUID() })
  if (!valid) throw new TypeError('brouillon invalide')
  await setMeta('draft', valid)
  return valid
}

/** Vrai si la prise date de plus de `MAX_DRAFT_AGE_MS`, ou de plus de
 *  `MAX_DRAFT_FUTURE_MS` dans le futur. */
export function isDraftExpired(draft: Draft, now: number): boolean {
  const age = now - Date.parse(draft.capturedAt)
  return age > MAX_DRAFT_AGE_MS || age < -MAX_DRAFT_FUTURE_MS
}

/** Brouillon gardé et valide. Un brouillon d'avant la story 1.13, sans Identifiant client,
 *  en reçoit un à sa première lecture (gardé : le même ensuite). Lecture et écriture dans
 *  une même transaction : deux onglets ne lui attribuent pas deux Identifiants. */
async function readDraft(): Promise<Draft | undefined> {
  return db.transaction('rw', db.meta, async () => {
    const value = (await db.meta.get('draft'))?.value
    const draft = parseDraft(value)
    if (draft || value === null || typeof value !== 'object' || 'clientUuid' in value) {
      return draft
    }
    const completed = parseDraft({ ...value, clientUuid: crypto.randomUUID() })
    if (completed) await db.meta.put({ key: 'draft', value: completed })
    return completed
  })
}

/** Brouillon gardé, valide et non périmé ; `undefined` s'il manque, n'a pas la forme
 *  attendue ou est périmé (il est alors effacé). */
export async function getDraft(now: number = Date.now()): Promise<Draft | undefined> {
  const draft = await readDraft()
  if (draft && isDraftExpired(draft, now)) {
    await clearDraft()
    return undefined
  }
  return draft
}

export async function clearDraft(): Promise<void> {
  await deleteMeta('draft')
}
