// Création d'un Signalement : `POST /v1/reports` (multipart : `meta`, `photo`, `voice`).
// Client écrit à la main pour la démo ; le client généré depuis l'OpenAPI (story 1.13,
// reporté) le remplacera. `fetch` n'est permis qu'ici et dans `src/offline/`.
import { ensureDeviceId } from '../offline/device.ts'

export const REPORTS_PATH = '/v1/reports'
export const SEND_TIMEOUT_MS = 30_000

export type PileSize = 'small' | 'medium' | 'large'

export interface ReportMeta {
  client_uuid: string
  lat: number
  lng: number
  accuracy_m: number
  captured_at: string
  pile_size: PileSize
  comment?: string
  waste_type?: string
  consent: { terms: boolean; training: boolean }
}

export interface ReportCreated {
  id: string
  tracking_number: string
  status: string
  received_at: string
  is_demo: boolean
}

export type SendResult =
  | { ok: true; report: ReportCreated }
  /** `code` : code d'erreur de l'API, ou `network` (pas de réponse, délai, 5xx illisible). */
  | { ok: false; status: number; code: string }

function isCreated(value: unknown): value is ReportCreated {
  if (value === null || typeof value !== 'object') return false
  const v = value as Record<string, unknown>
  return (
    typeof v.id === 'string' &&
    typeof v.tracking_number === 'string' &&
    typeof v.status === 'string' &&
    typeof v.received_at === 'string' &&
    typeof v.is_demo === 'boolean'
  )
}

async function errorCode(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { error?: { code?: unknown } }
    return typeof body.error?.code === 'string' ? body.error.code : 'network'
  } catch {
    return 'network'
  }
}

export async function sendReport(
  meta: ReportMeta,
  photo: Blob,
  voice: Blob | null,
  timeoutMs = SEND_TIMEOUT_MS,
): Promise<SendResult> {
  const form = new FormData()
  form.set('meta', JSON.stringify(meta))
  form.set('photo', photo, 'depot.jpg')
  if (voice) form.set('voice', voice, 'note.webm')

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const response = await fetch(REPORTS_PATH, {
      method: 'POST',
      body: form,
      headers: { 'X-Device-Id': await ensureDeviceId() },
      signal: controller.signal,
    })
    if (response.ok) {
      const body: unknown = await response.json()
      if (isCreated(body)) return { ok: true, report: body }
      return { ok: false, status: response.status, code: 'network' }
    }
    const code = response.status >= 500 ? 'network' : await errorCode(response)
    return { ok: false, status: response.status, code }
  } catch {
    return { ok: false, status: 0, code: 'network' }
  } finally {
    clearTimeout(timer)
  }
}
