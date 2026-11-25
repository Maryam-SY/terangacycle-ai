// Photo du dépôt (story 1.9) : parcours des marqueurs JPEG sur des octets synthétiques,
// refus d'une photo ancienne, boucle qualité puis dimensions. Le décodage et le canevas
// réels sont vérifiés dans Chromium (e2e/capture.spec.ts).
import { describe, expect, it } from 'vitest'

import {
  assertFreshPhoto,
  captureTime,
  encodeWithinLimit,
  fitWithin,
  hasApp1,
  hasMetadataSegments,
  JPEG_QUALITIES,
  MAX_EDGE_PX,
  MAX_PHOTO_AGE_MS,
  MAX_PHOTO_BYTES,
  processPhoto,
  readJpegSegments,
  StalePhotoError,
  UnreadablePhotoError,
  withoutMetadata,
} from './photo.ts'

const SOI = [0xff, 0xd8]
const EOI = [0xff, 0xd9]

/** Segment à longueur : marqueur, longueur sur 2 octets (elle-même comprise), contenu. */
function segment(marker: number, payload: number[]): number[] {
  const length = payload.length + 2
  return [0xff, marker, length >> 8, length & 0xff, ...payload]
}

const APP0 = segment(0xe0, [0x4a, 0x46, 0x49, 0x46, 0x00, 1, 1, 0, 0, 1, 0, 1, 0, 0])
// « Exif\0\0 » puis un en-tête TIFF minimal.
const APP1 = segment(0xe1, [0x45, 0x78, 0x69, 0x66, 0, 0, 0x4d, 0x4d, 0, 0x2a, 0, 0, 0, 8])
const ascii = (text: string) => [...text].map((char) => char.charCodeAt(0))
// Profil de couleurs (gardé) et autres segments de métadonnées (retirés).
const APP2_ICC = segment(0xe2, [...ascii('ICC_PROFILE'), 0, 1, 1, 0, 0, 0, 0])
const APP2_OTHER = segment(0xe2, [...ascii('MPF'), 0, 1, 2, 3])
const APP13 = segment(0xed, [...ascii('Photoshop 3.0'), 0, 0x38, 0x42, 0x49, 0x4d])
const COM = segment(0xfe, ascii('Pris au Plateau'))
const DQT = segment(0xdb, [0, ...new Array<number>(64).fill(1)])
const SOS = segment(0xda, [1, 1, 0, 0, 0x3f, 0])
const SCAN = [0x12, 0x34, 0xff, 0x00, 0x56]

function jpeg(...parts: number[][]): Uint8Array<ArrayBuffer> {
  return new Uint8Array([...SOI, ...parts.flat(), ...SOS, ...SCAN, ...EOI])
}

describe('readJpegSegments', () => {
  it('liste les segments d’en-tête jusqu’à SOS inclus', () => {
    const bytes = jpeg(APP0, DQT)
    const segments = readJpegSegments(bytes)
    expect(segments.map((s) => s.marker)).toEqual([0xe0, 0xdb, 0xda])
    expect(segments[0]).toEqual({ marker: 0xe0, offset: 2, length: APP0.length })
    expect(segments[1].offset).toBe(2 + APP0.length)
  })

  it('accepte les octets de remplissage 0xFF avant un marqueur', () => {
    const bytes = new Uint8Array([...SOI, 0xff, ...APP0, ...SOS, ...SCAN, ...EOI])
    expect(readJpegSegments(bytes).map((s) => s.marker)).toEqual([0xe0, 0xda])
  })

  it.each([
    ['vide', new Uint8Array()],
    ['sans SOI', new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a])],
    ['tronqué dans un segment', jpeg(APP0, DQT).subarray(0, 2 + APP0.length + 10)],
    ['tronqué juste après SOI', new Uint8Array([...SOI, 0xff])],
    ['tronqué dans les données (pas de EOI)', jpeg(APP0).subarray(0, -2)],
    ['sans SOS', new Uint8Array([...SOI, ...APP0, ...EOI])],
    ['longueur déclarée trop courte', new Uint8Array([...SOI, 0xff, 0xe0, 0, 1, ...EOI])],
    ['octet hors marqueur', new Uint8Array([...SOI, 0x00, ...APP0, ...SOS, ...EOI])],
  ])('JPEG malformé (%s) : UnreadablePhotoError', (_, bytes) => {
    expect(() => readJpegSegments(bytes)).toThrow(UnreadablePhotoError)
    expect(() => hasApp1(bytes)).toThrow(UnreadablePhotoError)
  })
})

describe('hasApp1, hasMetadataSegments et withoutMetadata', () => {
  it('sans métadonnées (JFIF et profil ICC seulement) : faux, octets rendus tels quels', () => {
    const bytes = jpeg(APP0, APP2_ICC, DQT)
    expect(hasApp1(bytes)).toBe(false)
    expect(hasMetadataSegments(bytes)).toBe(false)
    expect(withoutMetadata(bytes)).toBe(bytes)
  })

  it('avec APP1 (Exif) : vrai', () => {
    expect(hasApp1(jpeg(APP1, APP0, DQT))).toBe(true)
    expect(hasApp1(jpeg(APP0, APP1))).toBe(true)
  })

  it.each([
    ['APP1 (Exif)', APP1],
    ['APP13 (IPTC)', APP13],
    ['COM', COM],
    ['APP2 hors profil ICC', APP2_OTHER],
  ])('%s : segment de métadonnées', (_, metadata) => {
    expect(hasMetadataSegments(jpeg(APP0, metadata, DQT))).toBe(true)
  })

  it('withoutMetadata retire APP1, APP13, COM et l’APP2 non ICC, garde le reste à l’octet près', () => {
    const bytes = jpeg(APP1, APP0, APP2_ICC, APP13, APP1, COM, APP2_OTHER, DQT)
    const clean = withoutMetadata(bytes)
    expect(hasApp1(clean)).toBe(false)
    expect(hasMetadataSegments(clean)).toBe(false)
    expect([...clean]).toEqual([...jpeg(APP0, APP2_ICC, DQT)])
  })

  it('un octet 0xFF 0xE1 dans les données de l’image n’est pas un APP1', () => {
    const bytes = new Uint8Array([...SOI, ...APP0, ...SOS, 0xff, 0xe1, 0x00, ...EOI])
    expect(hasApp1(bytes)).toBe(false)
  })
})

describe('photo ancienne', () => {
  const now = Date.parse('2026-11-25T10:00:00Z')

  it('10 minutes exactement : acceptée ; au-delà : StalePhotoError', () => {
    expect(() => assertFreshPhoto(now - MAX_PHOTO_AGE_MS, now)).not.toThrow()
    expect(() => assertFreshPhoto(now - MAX_PHOTO_AGE_MS - 1, now)).toThrow(StalePhotoError)
    expect(() => assertFreshPhoto(now - 24 * 3600_000, now)).toThrow(StalePhotoError)
  })

  it('date dans le futur : acceptée jusqu’à 10 minutes, refusée au-delà ; illisible : refusée', () => {
    expect(() => assertFreshPhoto(now + 60_000, now)).not.toThrow()
    expect(() => assertFreshPhoto(now + MAX_PHOTO_AGE_MS, now)).not.toThrow()
    expect(() => assertFreshPhoto(now + MAX_PHOTO_AGE_MS + 1, now)).toThrow(StalePhotoError)
    expect(() => assertFreshPhoto(Number.NaN, now)).toThrow(StalePhotoError)
  })

  it('heure de la prise : lastModified, jamais après l’arrivée ; illisible : l’arrivée', () => {
    expect(captureTime(now - 5000, now)).toBe(now - 5000)
    expect(captureTime(now + 5000, now)).toBe(now)
    expect(captureTime(Number.NaN, now)).toBe(now)
  })

  it('processPhoto refuse une photo ancienne avant tout décodage', async () => {
    const file = new File([new Uint8Array(jpeg(APP0))], 'galerie.jpg', {
      type: 'image/jpeg',
      lastModified: now - 11 * 60_000,
    })
    await expect(processPhoto(file, now)).rejects.toBeInstanceOf(StalePhotoError)
  })

  it('processPhoto sans décodeur disponible : UnreadablePhotoError', async () => {
    const file = new File([new Uint8Array(jpeg(APP0))], 'photo.heic', {
      type: 'image/heic',
      lastModified: now,
    })
    await expect(processPhoto(file, now)).rejects.toBeInstanceOf(UnreadablePhotoError)
  })
})

describe('encodeWithinLimit', () => {
  /** Encodeur simulé : poids proportionnel aux pixels et à la qualité (seul `size` est lu,
   *  rien n'est alloué). */
  function fakeEncoder(bytesPerPixelAtFull: number) {
    const calls: [number, number, number][] = []
    const encode = (width: number, height: number, quality: number) => {
      calls.push([width, height, quality])
      const size = Math.round(width * height * bytesPerPixelAtFull * quality)
      return Promise.resolve({ size, type: 'image/jpeg' } as Blob)
    }
    return { calls, encode }
  }

  it('côté le plus long ramené à 1 600 px, proportions gardées', () => {
    expect(fitWithin(3000, 4000, MAX_EDGE_PX)).toEqual({ width: 1200, height: 1600 })
    expect(fitWithin(800, 600, MAX_EDGE_PX)).toEqual({ width: 800, height: 600 })
  })

  it('premier palier sous la limite : un seul encodage', async () => {
    const { calls, encode } = fakeEncoder(0.05)
    const result = await encodeWithinLimit(4000, 3000, encode)
    expect(calls).toEqual([[1600, 1200, JPEG_QUALITIES[0]]])
    expect(result).toMatchObject({ width: 1600, height: 1200 })
    expect(result.blob.size).toBeLessThanOrEqual(MAX_PHOTO_BYTES)
  })

  it('la qualité baisse d’abord, puis les dimensions, jusqu’à tenir sous la limite', async () => {
    const { calls, encode } = fakeEncoder(0.4)
    const result = await encodeWithinLimit(3000, 4000, encode)
    // Tous les paliers de qualité à 1 600 px, puis une taille réduite.
    expect(calls.slice(0, JPEG_QUALITIES.length)).toEqual(
      JPEG_QUALITIES.map((quality) => [1200, 1600, quality]),
    )
    expect(Math.max(result.width, result.height)).toBeLessThan(1600)
    expect(result.height).toBeGreaterThan(result.width)
    expect(result.blob.size).toBeLessThanOrEqual(MAX_PHOTO_BYTES)
    expect(calls.at(-1)).toEqual([result.width, result.height, expect.any(Number)])
  })

  it('impossible même petite : UnreadablePhotoError', async () => {
    const { encode } = fakeEncoder(1000)
    await expect(encodeWithinLimit(4000, 3000, encode)).rejects.toBeInstanceOf(
      UnreadablePhotoError,
    )
  })
})
