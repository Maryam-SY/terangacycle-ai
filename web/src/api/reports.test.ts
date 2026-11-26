import 'fake-indexeddb/auto'

import { afterEach, describe, expect, it, vi } from 'vitest'

import { sendReport, type ReportMeta } from './reports.ts'

const META: ReportMeta = {
  client_uuid: '0b1c9f42-5a1e-4e3b-9d70-3a7a8f8c2e11',
  lat: 14.6708,
  lng: -17.4381,
  accuracy_m: 12,
  captured_at: '2026-11-26T09:30:00.000Z',
  pile_size: 'medium',
  consent: { terms: true, training: false },
}
const CREATED = {
  id: '7f3c2a9e-1b64-4c0e-9a55-2d1f0c8e4a10',
  tracking_number: 'TC-2026-000001',
  status: 'pending_review',
  received_at: '2026-11-26T09:30:01Z',
  is_demo: true,
}

function mockFetch(response: Response | Error) {
  const fetchMock = vi.fn(() =>
    response instanceof Error ? Promise.reject(response) : Promise.resolve(response),
  )
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => vi.unstubAllGlobals())

describe('sendReport', () => {
  it('envoie meta, photo, note vocale et X-Device-Id, puis rend le Signalement créé', async () => {
    const fetchMock = mockFetch(new Response(JSON.stringify(CREATED), { status: 201 }))
    const photo = new Blob(['jpeg'], { type: 'image/jpeg' })
    const voice = new Blob(['webm'], { type: 'audio/webm' })

    const result = await sendReport(META, photo, voice)

    expect(result).toEqual({ ok: true, report: CREATED })
    const [path, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit]
    expect(path).toBe('/v1/reports')
    expect(init.method).toBe('POST')
    expect((init.headers as Record<string, string>)['X-Device-Id']).toMatch(/^[A-Za-z0-9_-]{43}$/)
    const form = init.body as FormData
    expect(JSON.parse(form.get('meta') as string)).toEqual(META)
    expect(form.get('photo')).toBeInstanceOf(Blob)
    expect(form.get('voice')).toBeInstanceOf(Blob)
  })

  it('n’envoie pas de partie voice sans note vocale', async () => {
    const fetchMock = mockFetch(new Response(JSON.stringify(CREATED), { status: 201 }))
    await sendReport(META, new Blob(['jpeg']), null)
    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit]
    expect((init.body as FormData).has('voice')).toBe(false)
  })

  it('rend le code d’erreur de l’API', async () => {
    mockFetch(
      new Response(JSON.stringify({ error: { code: 'outside_active_zone', message: 'x' } }), {
        status: 422,
      }),
    )
    expect(await sendReport(META, new Blob(['jpeg']), null)).toEqual({
      ok: false,
      status: 422,
      code: 'outside_active_zone',
    })
  })

  it('traite une panne réseau ou une erreur 5xx comme « network »', async () => {
    mockFetch(new TypeError('Failed to fetch'))
    expect(await sendReport(META, new Blob(['jpeg']), null)).toMatchObject({ code: 'network' })
    mockFetch(new Response('Bad gateway', { status: 502 }))
    expect(await sendReport(META, new Blob(['jpeg']), null)).toMatchObject({
      status: 502,
      code: 'network',
    })
  })
})
