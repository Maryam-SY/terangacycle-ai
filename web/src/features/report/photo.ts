// Photo du dépôt (story 1.9) : redressée selon son orientation, réduite et ré-encodée en
// JPEG d'au plus 300 Ko, sans aucune métadonnée. Le ré-encodage par un canevas n'écrit
// que les pixels : ni EXIF, ni GPS, ni modèle de l'appareil. Les octets rendus sont
// exactement ceux qui seront envoyés (story 1.13).
//
// Une photo que le navigateur ne sait pas décoder (HEIC sur Chrome Android, fichier
// corrompu) lève `PhotoUnreadableError` : rien n'est gardé, le Citoyen reprend la photo.

/** Plafond de NFR-4 : 300 Ko (307 200 octets). */
export const MAX_PHOTO_BYTES = 307_200

/** Côtés maximaux essayés, du plus grand au plus petit, puis qualités JPEG essayées. */
const MAX_SIDES = [1600, 1280, 1024, 800, 640] as const
const QUALITIES = [0.82, 0.7, 0.6, 0.5] as const

export class PhotoUnreadableError extends Error {
  constructor() {
    super('photo illisible')
    this.name = 'PhotoUnreadableError'
  }
}

export interface DecodedImage {
  width: number
  height: number
  close?: () => void
}

/** Décodage et encodage, remplaçables dans les tests (Vitest n'a pas de canevas). */
export interface PhotoCodec<I extends DecodedImage = DecodedImage> {
  /** Décode en appliquant l'orientation EXIF ; lève si le format n'est pas lisible. */
  decode: (file: Blob) => Promise<I>
  /** Dessine l'image à la taille donnée et l'encode en JPEG. */
  encode: (image: I, width: number, height: number, quality: number) => Promise<Blob>
}

/** Taille réduite qui garde les proportions, le plus grand côté valant au plus `maxSide`. */
export function fitWithin(width: number, height: number, maxSide: number) {
  const scale = Math.min(1, maxSide / Math.max(width, height))
  return {
    width: Math.max(1, Math.round(width * scale)),
    height: Math.max(1, Math.round(height * scale)),
  }
}

export async function preparePhoto<I extends DecodedImage>(
  file: Blob,
  codec: PhotoCodec<I>,
): Promise<Blob> {
  let image: I
  try {
    image = await codec.decode(file)
  } catch {
    throw new PhotoUnreadableError()
  }
  try {
    for (const maxSide of MAX_SIDES) {
      const { width, height } = fitWithin(image.width, image.height, maxSide)
      for (const quality of QUALITIES) {
        const jpeg = await codec.encode(image, width, height, quality)
        if (jpeg.size <= MAX_PHOTO_BYTES) return jpeg
      }
    }
  } catch {
    throw new PhotoUnreadableError()
  } finally {
    image.close?.()
  }
  // Même à 640 px et qualité 0,5 : image anormale (bruit pur), refusée plutôt qu'envoyée.
  throw new PhotoUnreadableError()
}

/** Codec du navigateur : `createImageBitmap` (orientation EXIF appliquée) et canevas. */
export const browserCodec: PhotoCodec<ImageBitmap> = {
  decode: (file) => createImageBitmap(file, { imageOrientation: 'from-image' }),
  encode: (image, width, height, quality) =>
    new Promise((resolve, reject) => {
      const canvas = document.createElement('canvas')
      canvas.width = width
      canvas.height = height
      const context = canvas.getContext('2d')
      if (!context) {
        reject(new Error('canevas indisponible'))
        return
      }
      context.drawImage(image, 0, 0, width, height)
      canvas.toBlob(
        (blob) => (blob ? resolve(blob) : reject(new Error('encodage impossible'))),
        'image/jpeg',
        quality,
      )
    }),
}

/** Vrai si un JPEG porte un segment EXIF ou XMP (APP1). Lit les en-têtes jusqu'aux données. */
export function jpegHasApp1(bytes: Uint8Array): boolean {
  if (bytes[0] !== 0xff || bytes[1] !== 0xd8) return false
  let pos = 2
  while (pos + 4 <= bytes.length && bytes[pos] === 0xff) {
    const marker = bytes[pos + 1]
    if (marker === 0xe1) return true
    if (marker === 0xda) return false // début des données d'image
    pos += 2 + ((bytes[pos + 2] << 8) | bytes[pos + 3])
  }
  return false
}
