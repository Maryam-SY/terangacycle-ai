// Règles de l'écran 3 (story 1.13), sans React : raison d'un envoi impossible, commentaire
// limité à 280 points de code, `meta` envoyé à POST /v1/reports et conduite à tenir pour
// chaque erreur de l'envoi.
import { ApiError, type ErrorMessageKey } from '../../api/client.ts'
import type { HeapSize, ReportMeta, WasteType } from '../../api/reports.ts'
import type { Draft } from '../../offline/draft.ts'

/** Commentaire : 280 caractères au plus, comptés en points de code (comme le serveur). */
export const COMMENT_MAX = 280

/** Ce qui manque pour envoyer, dans l'ordre où le Citoyen le voit. */
export type MissingField = 'photo' | 'position' | 'heapSize'

/** Premier élément manquant (photo, Position, Taille de tas), ou `undefined` si l'envoi
 *  est possible. */
export function missingField(
  draft: Pick<Draft, 'photo' | 'lat' | 'lng' | 'accuracy'> | undefined,
  heapSize: HeapSize | undefined,
): MissingField | undefined {
  if (!draft || !(draft.photo instanceof Blob) || draft.photo.size === 0) return 'photo'
  if (![draft.lat, draft.lng, draft.accuracy].every(Number.isFinite)) return 'position'
  if (!heapSize) return 'heapSize'
  return undefined
}

/** Longueur en points de code (un emoji compte pour un, comme côté serveur). */
export function codePointLength(text: string): number {
  return [...text].length
}

/** Texte saisi borné à `COMMENT_MAX` points de code. Déjà au maximum, toute frappe qui
 *  ajouterait un caractère est ignorée (la saisie précédente reste) ; un collage trop long
 *  est tronqué. */
export function limitComment(previous: string, next: string): string {
  if (codePointLength(next) <= COMMENT_MAX) return next
  if (codePointLength(previous) >= COMMENT_MAX) return previous
  return [...next].slice(0, COMMENT_MAX).join('')
}

export interface Choices {
  heapSize: HeapSize
  wasteType?: WasteType
  comment: string
}

/** `meta` de POST /v1/reports. `comment` seulement s'il n'est pas vide, `waste_type`
 *  seulement s'il est choisi ; `consent` lu au moment de l'envoi. */
export function buildMeta(
  draft: Draft,
  { heapSize, wasteType, comment }: Choices,
  consent: { terms: boolean; training: boolean },
): ReportMeta {
  const meta: ReportMeta = {
    client_uuid: draft.clientUuid,
    lat: draft.lat,
    lng: draft.lng,
    accuracy_m: draft.accuracy,
    captured_at: draft.capturedAt,
    heap_size: heapSize,
    consent: { terms: consent.terms, training: consent.training },
  }
  const trimmed = comment.trim()
  if (trimmed !== '') meta.comment = trimmed
  if (wasteType) meta.waste_type = wasteType
  return meta
}

/** Conduite à tenir après un envoi refusé ou sans réponse :
 *  - `retry` : erreur réseau ou serveur, la saisie est gardée et le même envoi repart ;
 *  - `outside-zone` : message et retour à l'écran 2 ;
 *  - `consent` : retour à l'écran de consentement ;
 *  - `retake` : photo refusée, message et invitation à reprendre la photo ;
 *  - `message` : tout autre refus, son message, brouillon gardé. */
export type SendFailure =
  | { kind: 'retry'; messageKey: 'details.networkError' }
  | { kind: 'outside-zone'; messageKey: ErrorMessageKey }
  | { kind: 'consent' }
  | { kind: 'retake'; messageKey: ErrorMessageKey }
  | { kind: 'message'; messageKey: ErrorMessageKey }

export function sendFailure(error: unknown): SendFailure {
  // Réseau coupé, délai dépassé, ou toute autre erreur imprévue : la saisie reste, on
  // peut réessayer.
  if (!(error instanceof ApiError) || error.isServerError) {
    return { kind: 'retry', messageKey: 'details.networkError' }
  }
  const { status, code, messageKey } = error
  if (status === 422 && code === 'outside_active_zone') return { kind: 'outside-zone', messageKey }
  if (status === 422 && code === 'consent_required') return { kind: 'consent' }
  // 413 (photo trop lourde), 415 (format refusé), 422 `photo_*` (trop de pixels, illisible).
  if (status === 413 || status === 415 || (status === 422 && code.startsWith('photo_'))) {
    return { kind: 'retake', messageKey }
  }
  return { kind: 'message', messageKey }
}
