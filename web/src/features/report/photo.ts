// Photo du dépôt (story 1.9), traitée sur l'appareil avant d'être gardée en brouillon :
// décodage par le navigateur (HEIC compris là où il est lu), orientation appliquée,
// réduction et ré-encodage en JPEG d'au plus 300 Ko par un canevas. Un canevas n'écrit ni
// Exif, ni XMP, ni GPS ; par sûreté, tout segment de métadonnées est encore retiré du JPEG
// produit (seuls JFIF et le profil de couleurs ICC restent). Les octets produits ici sont
// ceux qui sont gardés puis envoyés, sans autre ré-encodage.
// Donnée personnelle : aucun octet de photo n'est écrit dans la console.

/** Poids maximal du JPEG produit (300 Kio). */
export const MAX_PHOTO_BYTES = 307_200
/** Côté le plus long visé. */
export const MAX_EDGE_PX = 1600
/** En dessous, la photo ne serait plus exploitable : abandon. */
export const MIN_EDGE_PX = 320
/** Prise de vue directe : une photo plus ancienne vient d'ailleurs (galerie, autre lieu). */
export const MAX_PHOTO_AGE_MS = 10 * 60_000
/** Âge maximal de la Position gardée avec la photo, à l'arrivée du fichier : le suivi de
 *  la Position s'arrête souvent pendant que l'appareil photo est ouvert. */
export const MAX_PHOTO_FIX_AGE_MS = 2 * 60_000
/** Paliers de qualité, essayés dans l'ordre à chaque taille. */
export const JPEG_QUALITIES = [0.85, 0.75, 0.65, 0.55] as const
/** Réduction des dimensions quand aucun palier de qualité ne tient sous la limite. */
export const SHRINK_FACTOR = 0.8

const JPEG_TYPE = 'image/jpeg'
const MARKER_SOI = 0xd8
const MARKER_EOI = 0xd9
const MARKER_SOS = 0xda
const MARKER_APP0 = 0xe0
const MARKER_APP1 = 0xe1
const MARKER_APP2 = 0xe2
const MARKER_APP15 = 0xef
const MARKER_COM = 0xfe
/** « ICC_PROFILE » suivi d'un octet nul : en-tête d'un APP2 qui porte le profil de couleurs. */
const ICC_PROFILE = [0x49, 0x43, 0x43, 0x5f, 0x50, 0x52, 0x4f, 0x46, 0x49, 0x4c, 0x45, 0x00]

/** Photo illisible : format non décodé (HEIC hors Safari), octets corrompus, échec du
 *  canevas. Rien n'est gardé. */
export class UnreadablePhotoError extends Error {
  constructor(options?: { cause?: unknown }) {
    super('photo illisible', options)
    this.name = 'UnreadablePhotoError'
  }
}

/** Photo trop ancienne : pas une prise de vue directe. Rien n'est gardé. */
export class StalePhotoError extends Error {
  constructor() {
    super('photo trop ancienne : prise de vue directe attendue')
    this.name = 'StalePhotoError'
  }
}

export interface ProcessedPhoto {
  /** JPEG d'au plus `MAX_PHOTO_BYTES` octets, sans segment de métadonnées. */
  blob: Blob
  width: number
  height: number
}

/** Refuse une photo dont `lastModified` s'écarte de `now` de plus de `MAX_PHOTO_AGE_MS`,
 *  avant comme après (horloge très décalée, date forgée), ou est illisible. */
export function assertFreshPhoto(lastModified: number, now: number): void {
  if (!Number.isFinite(lastModified) || Math.abs(now - lastModified) > MAX_PHOTO_AGE_MS) {
    throw new StalePhotoError()
  }
}

/** Heure de la prise : `lastModified` du fichier s'il est lisible, jamais après `now`
 *  (heure de son arrivée dans la page). */
export function captureTime(lastModified: number, now: number): number {
  return Number.isFinite(lastModified) ? Math.min(lastModified, now) : now
}

/** Dimensions réduites pour que le côté le plus long tienne dans `maxEdge` (jamais agrandies). */
export function fitWithin(
  width: number,
  height: number,
  maxEdge: number,
): { width: number; height: number } {
  const scale = Math.min(1, maxEdge / Math.max(width, height))
  return {
    width: Math.max(1, Math.round(width * scale)),
    height: Math.max(1, Math.round(height * scale)),
  }
}

/** Encode l'image aux dimensions et à la qualité données. */
export type Encoder = (width: number, height: number, quality: number) => Promise<Blob>

/** Premier encodage sous `limit` : la qualité baisse par paliers, puis les dimensions
 *  (×0,8), en partant d'un côté le plus long de `MAX_EDGE_PX` au plus. */
export async function encodeWithinLimit(
  width: number,
  height: number,
  encode: Encoder,
  limit: number = MAX_PHOTO_BYTES,
): Promise<ProcessedPhoto> {
  let size = fitWithin(width, height, MAX_EDGE_PX)
  for (;;) {
    for (const quality of JPEG_QUALITIES) {
      const blob = await encode(size.width, size.height, quality)
      if (blob.size <= limit) return { blob, ...size }
    }
    const edge = Math.floor(Math.max(size.width, size.height) * SHRINK_FACTOR)
    if (edge < MIN_EDGE_PX) throw new UnreadablePhotoError()
    size = fitWithin(size.width, size.height, edge)
  }
}

export interface JpegSegment {
  /** Code du marqueur (0xE1 pour APP1, 0xDA pour SOS…). */
  marker: number
  /** Position du premier octet 0xFF du marqueur. */
  offset: number
  /** Longueur totale, marqueur compris (pour SOS : l'en-tête seulement). */
  length: number
}

/** Segments d'en-tête d'un JPEG complet, de SOI jusqu'à SOS inclus. Lève
 *  `UnreadablePhotoError` si les octets ne forment pas un JPEG entier : SOI absent,
 *  segment tronqué, aucun SOS, ou pas de EOI final. */
export function readJpegSegments(bytes: Uint8Array): JpegSegment[] {
  const malformed = () => new UnreadablePhotoError()
  if (bytes.length < 4 || bytes[0] !== 0xff || bytes[1] !== MARKER_SOI) throw malformed()
  const segments: JpegSegment[] = []
  let offset = 2
  for (;;) {
    if (offset >= bytes.length || bytes[offset] !== 0xff) throw malformed()
    // Octets de remplissage 0xFF permis avant le code du marqueur.
    let codeAt = offset + 1
    while (codeAt < bytes.length && bytes[codeAt] === 0xff) codeAt += 1
    if (codeAt >= bytes.length) throw malformed()
    const marker = bytes[codeAt]
    if (marker === 0x00 || marker === MARKER_SOI || marker === MARKER_EOI) throw malformed()
    if (marker === 0x01 || (marker >= 0xd0 && marker <= 0xd7)) {
      // Marqueur autonome, sans longueur.
      segments.push({ marker, offset, length: codeAt + 1 - offset })
      offset = codeAt + 1
      continue
    }
    if (codeAt + 2 >= bytes.length) throw malformed()
    const declared = (bytes[codeAt + 1] << 8) | bytes[codeAt + 2]
    const end = codeAt + 1 + declared
    if (declared < 2 || end > bytes.length) throw malformed()
    segments.push({ marker, offset, length: end - offset })
    if (marker === MARKER_SOS) break
    offset = end
  }
  if (bytes[bytes.length - 2] !== 0xff || bytes[bytes.length - 1] !== MARKER_EOI) throw malformed()
  return segments
}

/** Vrai si le JPEG porte un segment APP1 (Exif ou XMP). */
export function hasApp1(bytes: Uint8Array): boolean {
  return readJpegSegments(bytes).some((segment) => segment.marker === MARKER_APP1)
}

/** Vrai si le segment porte des métadonnées : tout APPn (Exif, XMP, IPTC/APP13…) sauf
 *  APP0 (JFIF) et un APP2 de profil ICC, et tout commentaire (COM). */
function isMetadata(bytes: Uint8Array, { marker, offset }: JpegSegment): boolean {
  if (marker === MARKER_COM) return true
  if (marker < MARKER_APP0 || marker > MARKER_APP15 || marker === MARKER_APP0) return false
  if (marker !== MARKER_APP2) return true
  // Contenu après le code du marqueur (octets de remplissage sautés) et la longueur.
  let codeAt = offset + 1
  while (bytes[codeAt] === 0xff) codeAt += 1
  const payload = codeAt + 3
  return !ICC_PROFILE.every((byte, index) => bytes[payload + index] === byte)
}

/** Vrai si le JPEG porte un segment de métadonnées (voir `withoutMetadata`). */
export function hasMetadataSegments(bytes: Uint8Array): boolean {
  return readJpegSegments(bytes).some((segment) => isMetadata(bytes, segment))
}

/** Le même JPEG sans ses segments de métadonnées : tout APPn sauf APP0 (JFIF) et le
 *  profil ICC (APP2), et tout COM. Les autres octets sont inchangés. */
export function withoutMetadata(bytes: Uint8Array<ArrayBuffer>): Uint8Array<ArrayBuffer> {
  const segments = readJpegSegments(bytes)
  if (!segments.some((segment) => isMetadata(bytes, segment))) return bytes
  const sos = segments[segments.length - 1]
  const kept = [bytes.subarray(0, 2)]
  for (const segment of segments) {
    if (!isMetadata(bytes, segment)) {
      kept.push(bytes.subarray(segment.offset, segment.offset + segment.length))
    }
  }
  kept.push(bytes.subarray(sos.offset + sos.length))
  const result = new Uint8Array(kept.reduce((sum, part) => sum + part.length, 0))
  let at = 0
  for (const part of kept) {
    result.set(part, at)
    at += part.length
  }
  return result
}

interface Decoded {
  source: CanvasImageSource
  width: number
  height: number
  release: () => void
}

/** Décodage avec orientation : `createImageBitmap`, sinon une image `<img>` (qui applique
 *  aussi l'orientation, `image-orientation: from-image` par défaut). */
async function decode(file: Blob): Promise<Decoded> {
  if (typeof createImageBitmap === 'function') {
    try {
      const bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' })
      return {
        source: bitmap,
        width: bitmap.width,
        height: bitmap.height,
        release: () => bitmap.close(),
      }
    } catch {
      // Repli sur <img> ci-dessous.
    }
  }
  if (typeof document === 'undefined') throw new UnreadablePhotoError()
  const url = URL.createObjectURL(file)
  const image = new Image()
  image.decoding = 'async'
  image.src = url
  try {
    await image.decode()
  } catch (cause) {
    URL.revokeObjectURL(url)
    throw new UnreadablePhotoError({ cause })
  }
  return {
    source: image,
    width: image.naturalWidth,
    height: image.naturalHeight,
    release: () => URL.revokeObjectURL(url),
  }
}

/** Encodeur sur un canevas réutilisé : l'image n'est redessinée que si les dimensions
 *  changent. Chaque JPEG est vérifié (structure) et débarrassé de toute métadonnée. */
function canvasEncoder(source: CanvasImageSource): { encode: Encoder; release: () => void } {
  const canvas = document.createElement('canvas')
  const context = canvas.getContext('2d')
  if (!context) throw new UnreadablePhotoError()
  let drawn = ''

  const encode: Encoder = async (width, height, quality) => {
    const key = `${width}x${height}`
    if (drawn !== key) {
      canvas.width = width
      canvas.height = height
      // Fond blanc : une image transparente (PNG) ne devient pas noire en JPEG.
      context.fillStyle = 'white'
      context.fillRect(0, 0, width, height)
      context.imageSmoothingEnabled = true
      context.imageSmoothingQuality = 'high'
      context.drawImage(source, 0, 0, width, height)
      drawn = key
    }
    const blob = await new Promise<Blob | null>((resolve) => {
      canvas.toBlob(resolve, JPEG_TYPE, quality)
    })
    if (!blob || blob.type !== JPEG_TYPE) throw new UnreadablePhotoError()
    const bytes = new Uint8Array(await blob.arrayBuffer())
    const clean = withoutMetadata(bytes)
    return clean === bytes ? blob : new Blob([clean], { type: JPEG_TYPE })
  }

  return {
    encode,
    release: () => {
      // Libère la mémoire du canevas sans attendre le ramasse-miettes.
      canvas.width = 0
      canvas.height = 0
    },
  }
}

/** Photo prête à garder : refus si trop ancienne (`StalePhotoError`), sinon décodée,
 *  orientée, réduite et ré-encodée sous `MAX_PHOTO_BYTES` ; tout échec de lecture ou
 *  d'encodage devient `UnreadablePhotoError`. `now` : heure du choix du fichier. */
export async function processPhoto(
  file: Blob & { lastModified: number },
  now: number,
): Promise<ProcessedPhoto> {
  assertFreshPhoto(file.lastModified, now)
  try {
    const decoded = await decode(file)
    try {
      if (!(decoded.width > 0 && decoded.height > 0)) throw new UnreadablePhotoError()
      const canvas = canvasEncoder(decoded.source)
      try {
        return await encodeWithinLimit(decoded.width, decoded.height, canvas.encode)
      } finally {
        canvas.release()
      }
    } finally {
      decoded.release()
    }
  } catch (error) {
    if (error instanceof UnreadablePhotoError) throw error
    throw new UnreadablePhotoError({ cause: error })
  }
}
