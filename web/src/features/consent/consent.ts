// Consentement du Citoyen (FR-4), mémorisé sur l'appareil seulement (Dexie `meta`).
// La story 1.11 le copiera sur chaque Signalement ; aucune requête ici.
import { getMeta, setMeta } from '../../offline/db.ts'

/** Version datée du texte de consentement. La changer quand le texte change : le
 *  consentement est alors redemandé à tous. */
export const CONSENT_VERSION = '2026-11-25'

/** SHA-256 des textes `consent.*` de fr.json (lignes `clé=valeur` triées) pour
 *  CONSENT_VERSION. Vérifié par consent.test.ts : un texte modifié sans nouvelle version
 *  fait échouer les tests. */
export const CONSENT_TEXT_SHA256 = '1849178c0d566df20962abe191b67c5db7efd54cd7049f040b580735947263b7'

export interface StoredConsent {
  /** Date de l'appareil, ISO 8601. */
  acceptedAt: string
  version: string
  /** Accord pour le réentraînement du Modèle (case séparée, non cochée par défaut). */
  training: boolean
}

function isStoredConsent(value: unknown): value is StoredConsent {
  if (value === null || typeof value !== 'object') return false
  const { acceptedAt, version, training } = value as Record<string, unknown>
  return typeof acceptedAt === 'string' && typeof version === 'string' && typeof training === 'boolean'
}

/** Consentement mémorisé, quelle que soit sa version ; `undefined` s'il manque ou est illisible. */
export async function getConsent(): Promise<StoredConsent | undefined> {
  const value = await getMeta('consent')
  return isStoredConsent(value) ? value : undefined
}

export async function acceptConsent({ training }: { training: boolean }): Promise<StoredConsent> {
  const consent: StoredConsent = {
    acceptedAt: new Date().toISOString(),
    version: CONSENT_VERSION,
    training,
  }
  await setMeta('consent', consent)
  return consent
}

/** Vrai si la version courante du texte a été acceptée, à une date lisible. */
export async function hasCurrentConsent(): Promise<boolean> {
  const consent = await getConsent()
  return consent?.version === CONSENT_VERSION && !Number.isNaN(Date.parse(consent.acceptedAt))
}
