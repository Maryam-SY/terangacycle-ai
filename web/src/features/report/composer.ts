// Règles pures de la barre de description (écran 3) : commentaire compté en points de code
// (comme le serveur), note vocale de 30 s au plus. Testées sans navigateur.

export const COMMENT_MAX = 280
export const VOICE_MAX_SECONDS = 30

/** Formats d'enregistrement essayés, dans l'ordre ; tous acceptés par le serveur. */
export const VOICE_MIME_TYPES = [
  'audio/webm;codecs=opus',
  'audio/webm',
  'audio/ogg;codecs=opus',
  'audio/mp4',
] as const

/** Nombre de caractères tel que le compte le serveur (points de code, pas unités UTF-16). */
export function codePointLength(text: string): number {
  return Array.from(text).length
}

/** Coupe la saisie à `max` points de code : un emoji n'est jamais coupé en deux. */
export function clampCodePoints(text: string, max = COMMENT_MAX): string {
  const points = Array.from(text)
  return points.length <= max ? text : points.slice(0, max).join('')
}

/** Premier format pris en charge par l'appareil, sinon `undefined` (choix du navigateur). */
export function pickVoiceMimeType(isSupported: (type: string) => boolean): string | undefined {
  return VOICE_MIME_TYPES.find((type) => isSupported(type))
}

/** Durée affichée « m:ss ». */
export function formatDuration(seconds: number): string {
  const whole = Math.max(0, Math.floor(seconds))
  return `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, '0')}`
}
