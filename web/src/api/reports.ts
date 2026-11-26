// Envoi d'un Signalement (story 1.13) : POST /v1/reports en multipart/form-data, `meta`
// (JSON du schéma ReportMeta) et `photo` (les octets exacts du brouillon).
// Donnée personnelle (Position, photo) : rien n'est écrit dans la console.
import { client, send } from './client.ts'
import type { components } from './schema'

export const REPORTS_PATH = '/v1/reports'
export const PHOTO_FILENAME = 'photo.jpg'

export type ReportMeta = components['schemas']['ReportMeta']
export type ReportCreated = components['schemas']['ReportCreated']
export type HeapSize = components['schemas']['HeapSize']
export type WasteType = components['schemas']['WasteType']

export interface SentReport {
  report: ReportCreated
  /** Vrai pour un renvoi reconnu par le serveur (200) : le Signalement existait déjà. */
  replayed: boolean
}

/** Corps multipart : `meta` en texte JSON (le serveur le lit comme un champ de
 *  formulaire, pas comme un fichier) et la photo telle quelle, nommée `photo.jpg`. */
export function reportFormData(meta: ReportMeta, photo: Blob): FormData {
  const form = new FormData()
  form.append('meta', JSON.stringify(meta))
  form.append('photo', photo, PHOTO_FILENAME)
  return form
}

/** POST /v1/reports. 201 (créé) ou 200 (renvoi du même Identifiant client) ; sinon
 *  `ApiError` ou `NetworkError` (client.ts). */
export async function sendReport(meta: ReportMeta, photo: Blob): Promise<SentReport> {
  const { data, status } = await send((signal) =>
    client.POST(REPORTS_PATH, {
      body: { meta, photo },
      bodySerializer: (body) => reportFormData(body.meta, body.photo),
      signal,
    }),
  )
  return { report: data, replayed: status === 200 }
}
