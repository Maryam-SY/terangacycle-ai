// Base locale de l'appareil (Dexie, IndexedDB). Version 1 : la table `meta`, réglages
// clé → valeur (Identifiant d'appareil, consentement, dernière configuration publique
// reçue de l'API). Les tables suivantes (file
// hors-ligne, Mes Signalements) arriveront par de nouvelles versions du schéma.
import Dexie, { type EntityTable } from 'dexie'

export const DB_NAME = 'terangacycle'

/** Clés connues de `meta` : une faute de frappe est refusée à la compilation. */
export type MetaKey = 'deviceId' | 'consent' | 'publicConfig'

export interface MetaRow {
  key: MetaKey
  value: unknown
}

export const db = new Dexie(DB_NAME) as Dexie & { meta: EntityTable<MetaRow, 'key'> }

db.version(1).stores({ meta: 'key' })

/** Valeur brute de `meta[key]`, `undefined` si absente. À valider par l'appelant. */
export async function getMeta(key: MetaKey): Promise<unknown> {
  const row = await db.meta.get(key)
  return row?.value
}

export async function setMeta(key: MetaKey, value: unknown): Promise<void> {
  await db.meta.put({ key, value })
}

/** Demande au navigateur de ne pas effacer la base sous pression d'espace. Sans attente
 *  ni erreur : un refus ou une API absente ne change rien au parcours. */
export function requestPersistentStorage(): void {
  try {
    void navigator.storage?.persist?.().catch(() => undefined)
  } catch {
    // API absente ou refusée : le stockage reste « au mieux ».
  }
}
