import { useEffect, useId, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Navigate, useNavigate } from 'react-router'

import { sendReport, type PileSize } from '../../api/reports.ts'
import fr from '../../i18n/fr.json'
import { PATHS } from '../../paths.ts'
import { AlertIcon, CheckIcon, PileIcon, SendIcon } from '../../ui/icons.tsx'
import { useFocusOnMount } from '../../ui/useFocusOnMount.ts'
import { WasteTypePicker } from '../classify/WasteTypePicker.tsx'
import type { WasteType } from '../classify/wasteTypes.ts'
import { getConsent } from '../consent/consent.ts'
import { Composer } from './Composer.tsx'
import { getDraft, setLastReport, type ReportDraft } from './draft.ts'

// Écran 3 · Détails et envoi (story 1.13), adapté sans proposition IA : miniature, Taille
// de tas (obligatoire), Type de déchet (facultatif), description écrite ou vocale, puis
// « Envoyer ». Les erreurs disent quoi faire ; la saisie est gardée tant que l'app est
// ouverte.

const PILE_SIZES: { value: PileSize; level: 1 | 2 | 3 }[] = [
  { value: 'small', level: 1 },
  { value: 'medium', level: 2 },
  { value: 'large', level: 3 },
]

type SendState =
  | { stage: 'editing' }
  | { stage: 'sending' }
  | { stage: 'failed'; code: string }

type ApiErrorCode = keyof typeof fr.errors
const PHOTO_ERRORS = new Set<string>([
  'photo_too_large',
  'unsupported_media_type',
  'photo_too_many_pixels',
  'photo_unreadable',
])

function isKnownCode(code: string): code is ApiErrorCode {
  return Object.hasOwn(fr.errors, code)
}

/** Message de l'écran 3 pour un code d'erreur ; un code inconnu vaut une erreur réseau. */
function errorKey(
  code: string,
): 'details.errors.network' | 'details.errors.photo' | `errors.${ApiErrorCode}` {
  if (PHOTO_ERRORS.has(code)) return 'details.errors.photo'
  if (code !== 'network' && isKnownCode(code)) return `errors.${code}`
  return 'details.errors.network'
}

function DetailsForm({ draft }: { draft: ReportDraft }) {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const titleRef = useFocusOnMount<HTMLHeadingElement>()
  const pileId = useId()
  const reasonId = useId()
  const [pileSize, setPileSize] = useState<PileSize | null>(null)
  const [wasteType, setWasteType] = useState<WasteType | null>(null)
  const [comment, setComment] = useState('')
  const [voice, setVoice] = useState<Blob | null>(null)
  const [send, setSend] = useState<SendState>({ stage: 'editing' })
  const [photoUrl, setPhotoUrl] = useState<string>()

  useEffect(() => {
    const url = URL.createObjectURL(draft.photo)
    setPhotoUrl(url) // oxlint-disable-line react/set-state-in-effect -- ressource externe
    return () => URL.revokeObjectURL(url)
  }, [draft.photo])

  const missing = pileSize === null
  const sending = send.stage === 'sending'

  async function submit() {
    if (pileSize === null || sending) return
    setSend({ stage: 'sending' })
    const consent = await getConsent()
    if (!consent) {
      void navigate(PATHS.consent, { replace: true })
      return
    }
    const result = await sendReport(
      {
        client_uuid: draft.clientUuid,
        lat: draft.lat,
        lng: draft.lng,
        accuracy_m: draft.accuracy,
        captured_at: draft.capturedAt,
        pile_size: pileSize,
        ...(comment.trim() ? { comment } : {}),
        ...(wasteType ? { waste_type: wasteType } : {}),
        consent: { terms: true, training: consent.training },
      },
      draft.photo,
      voice,
    )
    if (result.ok) {
      setLastReport(result.report)
      void navigate(PATHS.confirmation, { replace: true })
      return
    }
    if (result.code === 'consent_required') {
      void navigate(PATHS.consent, { replace: true })
      return
    }
    setSend({ stage: 'failed', code: result.code })
  }

  const failedCode = send.stage === 'failed' ? send.code : null
  const photoError = failedCode !== null && errorKey(failedCode) === 'details.errors.photo'
  const button =
    'flex min-h-12 items-center justify-center gap-3 rounded-xl px-4 text-lg font-semibold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-900'

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col gap-5 px-4 py-6" lang={i18n.language}>
      <h1 ref={titleRef} tabIndex={-1} className="text-2xl font-bold text-brand-900 focus:outline-none">
        {t('details.title')}
      </h1>

      {photoUrl && (
        <img
          src={photoUrl}
          alt={t('capture.preview.alt')}
          className="h-40 w-full rounded-xl border border-line object-cover"
        />
      )}

      <fieldset className="flex flex-col gap-2" aria-labelledby={pileId}>
        <legend id={pileId} className="text-lg font-semibold text-brand-900">
          {t('details.pileSize.label')}
        </legend>
        <div className="grid grid-cols-3 gap-2">
          {PILE_SIZES.map(({ value, level }) => {
            const selected = pileSize === value
            return (
              <button
                key={value}
                type="button"
                aria-pressed={selected}
                onClick={() => setPileSize(value)}
                className={`relative flex min-h-20 flex-col items-center justify-center gap-1 rounded-xl border-2 p-2 text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-900 ${
                  selected ? 'border-brand-600 bg-mint' : 'border-line bg-surface'
                }`}
              >
                {selected && <CheckIcon className="absolute top-1 right-1 size-5 text-brand-600" />}
                <PileIcon level={level} className="size-8 text-brand-600" />
                <span className="font-semibold">{t(`details.pileSize.${value}`)}</span>
              </button>
            )
          })}
        </div>
      </fieldset>

      <WasteTypePicker value={wasteType} onChange={setWasteType} />

      <Composer comment={comment} onComment={setComment} voice={voice} onVoice={setVoice} />

      {failedCode !== null && (
        <div role="alert" className="flex flex-col gap-3">
          <p className="flex gap-2 text-ink">
            <AlertIcon className="size-6 shrink-0 stroke-danger" />
            <span>{t(errorKey(failedCode))}</span>
          </p>
          {(failedCode === 'outside_active_zone' || photoError) && (
            <button
              type="button"
              onClick={() => void navigate(PATHS.capture, { replace: true })}
              className={`${button} border-2 border-brand-600 bg-surface text-brand-600`}
            >
              {t(photoError ? 'capture.preview.retake' : 'details.errors.backToCapture')}
            </button>
          )}
        </div>
      )}

      <div className="mt-auto flex flex-col gap-2 pt-2">
        {missing && (
          <p id={reasonId} className="text-sm text-muted">
            {t('details.missingPileSize')}
          </p>
        )}
        <button
          type="button"
          disabled={missing || sending}
          aria-describedby={missing ? reasonId : undefined}
          onClick={() => void submit()}
          className={`${button} bg-brand-600 text-surface disabled:cursor-not-allowed disabled:bg-mint disabled:text-muted`}
        >
          <SendIcon className="size-6 shrink-0" />
          {t(sending ? 'details.sending' : failedCode === 'network' ? 'details.retry' : 'details.send')}
        </button>
      </div>
    </main>
  )
}

/** Écran 3. Sans brouillon (lien direct, rechargement) : retour à la capture. */
export function DetailsPage() {
  const draft = getDraft()
  if (draft === null) return <Navigate to={PATHS.capture} replace />
  return <DetailsForm draft={draft} />
}
