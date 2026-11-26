import { describe, expect, it } from 'vitest'

import {
  MAX_PHOTO_BYTES,
  PhotoUnreadableError,
  fitWithin,
  jpegHasApp1,
  preparePhoto,
  type DecodedImage,
  type PhotoCodec,
} from './photo.ts'

/** Codec factice : la taille du JPEG dépend de la surface et de la qualité. */
function fakeCodec(bytesPerPixel: number, image: DecodedImage = { width: 4000, height: 3000 }) {
  const calls: { width: number; height: number; quality: number }[] = []
  let closed = false
  const codec: PhotoCodec = {
    decode: async () => ({ ...image, close: () => (closed = true) }),
    encode: async (_image, width, height, quality) => {
      calls.push({ width, height, quality })
      return new Blob([new Uint8Array(Math.round(width * height * bytesPerPixel * quality))])
    },
  }
  return { codec, calls, isClosed: () => closed }
}

describe('preparePhoto', () => {
  it('rend un JPEG de 300 Ko au plus à partir d’une photo de 12 Mpx', async () => {
    const { codec, calls, isClosed } = fakeCodec(0.25)
    const jpeg = await preparePhoto(new Blob(['x']), codec)
    expect(jpeg.size).toBeLessThanOrEqual(MAX_PHOTO_BYTES)
    // Premier essai : 1600 px de grand côté, proportions gardées.
    expect(calls[0]).toEqual({ width: 1600, height: 1200, quality: 0.82 })
    expect(isClosed()).toBe(true)
  })

  it('réduit la qualité puis la taille jusqu’à tenir sous le plafond', async () => {
    const { codec, calls } = fakeCodec(0.6)
    const jpeg = await preparePhoto(new Blob(['x']), codec)
    expect(jpeg.size).toBeLessThanOrEqual(MAX_PHOTO_BYTES)
    expect(calls.length).toBeGreaterThan(1)
    expect(calls.at(-1)!.width).toBeLessThan(1600)
  })

  it('n’agrandit jamais une petite photo', async () => {
    const { codec, calls } = fakeCodec(0.1, { width: 640, height: 480 })
    await preparePhoto(new Blob(['x']), codec)
    expect(calls[0]).toMatchObject({ width: 640, height: 480 })
  })

  it('lève PhotoUnreadableError si la photo ne se décode pas (HEIC non pris en charge)', async () => {
    const codec: PhotoCodec = {
      decode: () => Promise.reject(new Error('format inconnu')),
      encode: () => Promise.reject(new Error('jamais appelé')),
    }
    await expect(preparePhoto(new Blob(['heic']), codec)).rejects.toBeInstanceOf(
      PhotoUnreadableError,
    )
  })

  it('lève PhotoUnreadableError si rien ne tient sous le plafond', async () => {
    const { codec, isClosed } = fakeCodec(50)
    await expect(preparePhoto(new Blob(['x']), codec)).rejects.toBeInstanceOf(
      PhotoUnreadableError,
    )
    expect(isClosed()).toBe(true)
  })
})

describe('fitWithin', () => {
  it('garde les proportions, en portrait comme en paysage', () => {
    expect(fitWithin(3000, 4000, 1600)).toEqual({ width: 1200, height: 1600 })
    expect(fitWithin(4000, 3000, 1600)).toEqual({ width: 1600, height: 1200 })
    expect(fitWithin(800, 600, 1600)).toEqual({ width: 800, height: 600 })
  })
})

describe('jpegHasApp1', () => {
  const soi = [0xff, 0xd8]
  const app0 = [0xff, 0xe0, 0x00, 0x04, 0x4a, 0x46]
  const app1 = [0xff, 0xe1, 0x00, 0x04, 0x45, 0x78]
  const sos = [0xff, 0xda, 0x00, 0x02]

  it('détecte un segment EXIF (APP1)', () => {
    expect(jpegHasApp1(new Uint8Array([...soi, ...app0, ...app1, ...sos]))).toBe(true)
  })

  it('ne voit rien sans APP1, ni dans les données après SOS', () => {
    expect(jpegHasApp1(new Uint8Array([...soi, ...app0, ...sos, 0xff, 0xe1]))).toBe(false)
  })
})
