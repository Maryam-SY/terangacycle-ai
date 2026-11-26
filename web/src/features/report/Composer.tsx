import { useEffect, useId, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'

import { AlertIcon, MicIcon, StopIcon, TrashIcon } from '../../ui/icons.tsx'
import {
  COMMENT_MAX,
  VOICE_MAX_SECONDS,
  clampCodePoints,
  codePointLength,
  formatDuration,
  pickVoiceMimeType,
} from './composer.ts'

// Barre de description de l'écran 3, comme la saisie de WhatsApp : on écrit, ou, quand le
// champ est vide, on touche le micro pour parler (wolof ou français) jusqu'à 30 s. Une
// note enregistrée s'écoute ou s'efface. Le micro n'est demandé qu'au premier toucher.

type Recording =
  | { state: 'idle' }
  | { state: 'recording'; seconds: number }
  | { state: 'denied' }

export function Composer({
  comment,
  onComment,
  voice,
  onVoice,
}: {
  comment: string
  onComment: (comment: string) => void
  voice: Blob | null
  onVoice: (voice: Blob | null) => void
}) {
  const { t } = useTranslation()
  const fieldId = useId()
  const hintId = useId()
  const [recording, setRecording] = useState<Recording>({ state: 'idle' })
  const recorderRef = useRef<MediaRecorder | null>(null)
  const [voiceUrl, setVoiceUrl] = useState<string>()

  // Adresse d'écoute de la note, libérée quand la note change ou que l'écran est quitté.
  useEffect(() => {
    if (!voice) return
    const url = URL.createObjectURL(voice)
    setVoiceUrl(url) // oxlint-disable-line react/set-state-in-effect -- ressource externe
    return () => URL.revokeObjectURL(url)
  }, [voice])

  // Arrêt automatique à 30 s ; compteur mis à jour chaque seconde.
  useEffect(() => {
    if (recording.state !== 'recording') return
    if (recording.seconds >= VOICE_MAX_SECONDS) {
      recorderRef.current?.stop()
      return
    }
    const timer = setTimeout(
      () => setRecording({ state: 'recording', seconds: recording.seconds + 1 }),
      1000,
    )
    return () => clearTimeout(timer)
  }, [recording])

  // En quittant l'écran pendant un enregistrement : micro libéré.
  useEffect(() => () => recorderRef.current?.stop(), [])

  async function startRecording() {
    let stream: MediaStream
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    } catch {
      setRecording({ state: 'denied' })
      return
    }
    const mimeType = pickVoiceMimeType((type) => MediaRecorder.isTypeSupported(type))
    const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
    const chunks: Blob[] = []
    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) chunks.push(event.data)
    }
    recorder.onstop = () => {
      stream.getTracks().forEach((track) => track.stop())
      recorderRef.current = null
      setRecording({ state: 'idle' })
      if (chunks.length > 0) onVoice(new Blob(chunks, { type: recorder.mimeType }))
    }
    recorderRef.current = recorder
    recorder.start()
    setRecording({ state: 'recording', seconds: 0 })
  }

  const round =
    'flex size-12 shrink-0 items-center justify-center rounded-full focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-900'

  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={fieldId} className="text-lg font-semibold text-brand-900">
        {t('details.describe.label')}{' '}
        <span className="text-base font-normal text-muted">{t('details.optional')}</span>
      </label>

      {voice && voiceUrl ? (
        <div className="flex items-center gap-2 rounded-3xl border-2 border-line bg-surface p-2">
          <audio controls src={voiceUrl} className="min-w-0 flex-1" aria-label={t('details.describe.listen')}>
            <track kind="captions" />
          </audio>
          <button
            type="button"
            onClick={() => onVoice(null)}
            aria-label={t('details.describe.deleteVoice')}
            className={`${round} border-2 border-line bg-surface text-ink`}
          >
            <TrashIcon />
          </button>
        </div>
      ) : (
        <div className="flex items-end gap-2">
          <div className="flex min-w-0 flex-1 flex-col rounded-3xl border-2 border-line bg-surface px-4 py-2">
            {recording.state === 'recording' ? (
              <p role="status" className="flex min-h-12 items-center gap-2 text-ink">
                <span className="size-3 shrink-0 animate-pulse rounded-full bg-danger" />
                {t('details.describe.recording', {
                  elapsed: formatDuration(recording.seconds),
                  max: formatDuration(VOICE_MAX_SECONDS),
                })}
              </p>
            ) : (
              <textarea
                id={fieldId}
                rows={2}
                value={comment}
                onChange={(event) => onComment(clampCodePoints(event.target.value))}
                aria-describedby={hintId}
                placeholder={t('details.describe.placeholder')}
                className="min-h-12 resize-none bg-transparent text-ink placeholder:text-muted focus:outline-none"
              />
            )}
          </div>
          {recording.state === 'recording' ? (
            <button
              type="button"
              onClick={() => recorderRef.current?.stop()}
              aria-label={t('details.describe.stop')}
              className={`${round} bg-brand-900 text-surface`}
            >
              <StopIcon />
            </button>
          ) : (
            comment.length === 0 && (
              <button
                type="button"
                onClick={() => void startRecording()}
                aria-label={t('details.describe.record')}
                className={`${round} bg-brand-600 text-surface`}
              >
                <MicIcon />
              </button>
            )
          )}
        </div>
      )}

      <p id={hintId} className="flex justify-between gap-2 text-sm text-muted">
        <span>{t('details.describe.hint')}</span>
        {!voice && (
          <span aria-live="polite">
            {codePointLength(comment)}/{COMMENT_MAX}
          </span>
        )}
      </p>
      {recording.state === 'denied' && (
        <p role="alert" className="flex gap-2 text-ink">
          <AlertIcon className="size-6 shrink-0 stroke-danger" />
          <span>{t('details.describe.micDenied')}</span>
        </p>
      )}
    </div>
  )
}
