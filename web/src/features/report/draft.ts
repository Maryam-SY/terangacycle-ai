// Brouillon de Signalement entre l'écran 2 (photo, Position) et l'écran 3 (détails et
// envoi, story 1.13). Gardé en mémoire seulement : un rechargement le perd, le Citoyen
// reprend la photo. La file hors-ligne (epic 6) gardera les Signalements à envoyer.

import type { ReportCreated } from '../../api/reports.ts'

export interface ReportDraft {
  /** Identifiant client (UUID v4), attribué à la création du brouillon, gardé pour tout renvoi. */
  clientUuid: string
  /** Octets exacts qui seront envoyés : JPEG ≤ 300 Ko, sans métadonnées. */
  photo: Blob
  lat: number
  lng: number
  /** Précision de la Position au moment de la prise de vue, en mètres. */
  accuracy: number
  /** Horodatage de l'appareil à la prise de vue, ISO 8601. */
  capturedAt: string
}

let current: ReportDraft | null = null

export function setDraft(draft: ReportDraft): void {
  current = draft
}

export function getDraft(): ReportDraft | null {
  return current
}

export function clearDraft(): void {
  current = null
}

// Dernier Signalement accepté, pour l'écran 4 · Confirmation.
let lastReport: ReportCreated | null = null

export function setLastReport(report: ReportCreated): void {
  lastReport = report
}

export function getLastReport(): ReportCreated | null {
  return lastReport
}

export function clearLastReport(): void {
  lastReport = null
}
