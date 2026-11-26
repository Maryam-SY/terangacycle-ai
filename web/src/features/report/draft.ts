// Brouillon de Signalement entre l'écran 2 (photo, Position) et l'écran 3 (détails et
// envoi, story 1.13). Gardé en mémoire seulement : un rechargement le perd, le Citoyen
// reprend la photo. La file hors-ligne (epic 6) gardera les Signalements à envoyer.

export interface ReportDraft {
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
