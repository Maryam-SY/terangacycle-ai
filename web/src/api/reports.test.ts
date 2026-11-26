// POST /v1/reports (story 1.13) : corps multipart (`meta` en JSON, photo telle quelle),
// 201 ou 200 (renvoi), erreurs traduites par le client.
import 'fake-indexeddb/auto'

import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiError, DEVICE_ID_HEADER } from './client.ts'
import { PHOTO_FILENAME, REPORTS_PATH, reportFormData, sendReport, type ReportMeta } from './reports.ts'

const JPEG = new Uint8Array([0xff, 0xd8, 0xff, 0xe0, 0, 16, 1, 2, 3, 250, 0xff, 0xd9])
const META: ReportMeta = {
  client_uuid: '0b8f3c52-7a4e-4f1d-9c3b-2e6a1d5f8a90',
  lat: 14.6708,
  lng: -17.4381,
  accuracy_m: 12,
  captured_at: '2026-11-26T10:00:00.000Z',
  heap_size: 'medium',
  waste_type: 'plastic',
  comment: 'Près de l’école 🙏',
  consent: { terms: true, training: false },
}
const CREATED = {
  id: '3f0c2a8e-5b9d-4c71-8e2f-6a1b0c9d7e54',
  tracking_number: 'TC-2026-000042',
  status: 'pending_review',
  received_at: '2026-11-26T10:00:05Z',
  is_demo: true,
}

function photo(): Blob {
  return new Blob([JPEG], { type: 'image/jpeg' })
}

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('reportFormData', () => {
  it('meta en texte JSON (champ de formulaire), photo nommée photo.jpg', async () => {
    const form = reportFormData(META, photo())
    expect([...form.keys()]).toEqual(['meta', 'photo'])
    const meta = form.get('meta')
    expect(typeof meta).toBe('string')
    expect(JSON.parse(meta as string)).toEqual(META)
    const sent = form.get('photo') as File
    expect(sent.name).toBe(PHOTO_FILENAME)
    expect(sent.type).toBe('image/jpeg')
    expect([...new Uint8Array(await sent.arrayBuffer())]).toEqual([...JPEG])
  })
})

describe('sendReport', () => {
  it('POST multipart vers /v1/reports, octets exacts du JPEG, X-Device-Id ; 201 → créé', async () => {
    const fetchSpy = vi.fn(async (_request: Request) => Response.json(CREATED, { status: 201 }))
    vi.stubGlobal('fetch', fetchSpy)
    await expect(sendReport(META, photo())).resolves.toEqual({ report: CREATED, replayed: false })

    expect(fetchSpy).toHaveBeenCalledOnce()
    const [request] = fetchSpy.mock.calls[0]
    expect(request.method).toBe('POST')
    expect(new URL(request.url).pathname).toBe(REPORTS_PATH)
    expect(request.headers.get('Content-Type')).toMatch(/^multipart\/form-data; boundary=/)
    expect(request.headers.get(DEVICE_ID_HEADER)).toMatch(/^[A-Za-z0-9_-]{43}$/)
    expect(request.headers.has('Authorization')).toBe(false)

    const form = await request.formData()
    expect(JSON.parse(form.get('meta') as string)).toEqual(META)
    const sent = form.get('photo') as File
    expect(sent.name).toBe(PHOTO_FILENAME)
    expect(sent.type).toBe('image/jpeg')
    expect([...new Uint8Array(await sent.arrayBuffer())]).toEqual([...JPEG])
  })

  it('200 : renvoi reconnu, même Signalement', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => Response.json(CREATED, { status: 200 })))
    await expect(sendReport(META, photo())).resolves.toEqual({ report: CREATED, replayed: true })
  })

  it('422 outside_active_zone : ApiError', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        Response.json(
          { error: { code: 'outside_active_zone', message: 'hors zone', request_id: 'r' } },
          { status: 422 },
        ),
      ),
    )
    const error: unknown = await sendReport(META, photo()).catch((reason: unknown) => reason)
    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status: 422, messageKey: 'errors.outside_active_zone' })
  })
})
