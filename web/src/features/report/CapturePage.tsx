import { useEffect, useId, useRef, useState, type ChangeEvent, type ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, Navigate, useNavigate } from 'react-router'

import { PATHS } from '../../paths.ts'
import { AlertIcon, CameraIcon, InfoIcon, LocationIcon, NoPersonIcon } from '../../ui/icons.tsx'
import { useFocusOnMount } from '../../ui/useFocusOnMount.ts'
import { useCurrentConsent } from '../consent/useCurrentConsent.ts'
import {
  assessCapture,
  canTakePhoto,
  keepsContinuation,
  type CaptureVerdict,
} from './capture.ts'
import { setDraft, type ReportDraft } from './draft.ts'
import { browserCodec, preparePhoto } from './photo.ts'
import { usePosition, type PositionState } from './usePosition.ts'
import { usePublicConfig } from './usePublicConfig.ts'

// Écran 2 · Capture (story 1.8) : Position suivie en haute précision, Zone active vérifiée
// sur l'appareil, déclencheur « Prendre la photo » actif seulement si la Position est
// utilisable. Story 1.9 : consigne « ni personne ni plaque » à chaque capture, prise de
// vue directe (appareil photo arrière), photo allégée sans métadonnées, aperçu, puis
// « Reprendre la photo » ou « Continuer » vers l'écran 3.

const BUTTON =
  'min-h-12 rounded-xl px-4 text-lg font-semibold focus-visible:outline-2 focus-visible:outline-offset-2'
const SECONDARY = `${BUTTON} self-start border-2 border-brand-600 bg-surface text-brand-600 focus-visible:outline-brand-900`
const SECONDARY_WIDE = `${BUTTON} border-2 border-brand-600 bg-surface text-brand-600 focus-visible:outline-brand-900`

/** Annonce des lecteurs d'écran, une par type d'état. */
const ANNOUNCEMENTS = {
  waiting: 'capture.announce.waiting',
  'position-error': 'capture.announce.positionError',
  'config-unavailable': 'capture.announce.configUnavailable',
  'outside-zone': 'capture.announce.outsideZone',
  imprecise: 'capture.announce.imprecise',
  ready: 'capture.announce.ready',
} as const satisfies Record<CaptureVerdict['kind'], string>

/** Message en Encre, icône à gauche : rouge pour un blocage, verte pour une information. */
function Message({ icon, children }: { icon: ReactNode; children: ReactNode }) {
  return (
    <div className="flex gap-3 text-ink">
      {icon}
      <div className="flex flex-col gap-3">{children}</div>
    </div>
  )
}

function Blocked({ id, text, onRetry }: { id: string; text: string; onRetry?: () => void }) {
  const { t } = useTranslation()
  return (
    <Message icon={<AlertIcon className="size-6 shrink-0 stroke-danger" />}>
      <p id={id}>{text}</p>
      {onRetry && (
        <button type="button" onClick={onRetry} className={SECONDARY}>
          {t('capture.retry')}
        </button>
      )}
    </Message>
  )
}

/** État de la Position et de la Zone. `textId` est posé sur la phrase qui explique l'état
 *  du déclencheur (lue avec lui par les lecteurs d'écran). */
function Status({
  textId,
  verdict,
  position,
  onRetryPosition,
  onRetryConfig,
  onContinue,
}: {
  textId: string
  verdict: CaptureVerdict
  position: PositionState
  onRetryPosition: () => void
  onRetryConfig: () => void
  onContinue: () => void
}) {
  const { t } = useTranslation()
  const located = <LocationIcon className="size-6 shrink-0 text-brand-600" />

  switch (verdict.kind) {
    case 'waiting':
      return (
        <Message icon={located}>
          <p id={textId}>
            {position.status === 'locating'
              ? t('capture.position.locating')
              : t('capture.zone.checking')}
          </p>
        </Message>
      )
    case 'position-error':
      return (
        <Blocked
          id={textId}
          text={
            verdict.reason === 'denied'
              ? t('capture.position.denied')
              : t('capture.position.unavailable')
          }
          onRetry={onRetryPosition}
        />
      )
    case 'config-unavailable':
      return <Blocked id={textId} text={t('capture.zone.firstConnection')} onRetry={onRetryConfig} />
    case 'outside-zone':
      return <Blocked id={textId} text={t('capture.zone.outside')} />
    case 'imprecise':
      return (
        <div className="flex flex-col gap-3">
          <Message icon={located}>
            <p>{t('capture.position.detected', { accuracy: verdict.accuracyM })}</p>
          </Message>
          <div className="flex flex-col gap-3 rounded-xl bg-warning-bg p-4 text-warning-ink">
            <p className="flex gap-3">
              <InfoIcon className="size-6 shrink-0" />
              <span id={textId}>{t('capture.position.wait')}</span>
            </p>
            <button
              type="button"
              onClick={onContinue}
              className={`${BUTTON} self-start border-2 border-warning-ink bg-warning-bg text-warning-ink focus-visible:outline-warning-ink`}
            >
              {t('capture.position.continue')}
            </button>
          </div>
        </div>
      )
    case 'ready':
      return (
        <Message icon={located}>
          <p id={textId}>{t('capture.position.detected', { accuracy: verdict.accuracyM })}</p>
        </Message>
      )
  }
}

type PhotoState =
  | { stage: 'none' }
  | { stage: 'processing' }
  | { stage: 'unreadable' }
  /** `url` : adresse locale de l'aperçu, libérée à la reprise ou en quittant l'écran. */
  | { stage: 'preview'; draft: ReportDraft; url: string }

/** Aperçu de la photo allégée : « Continuer » vers l'écran 3 ou « Reprendre la photo ». */
function PhotoPreview({
  url,
  onRetake,
  onContinue,
}: {
  url: string
  onRetake: () => void
  onContinue: () => void
}) {
  const { t } = useTranslation()
  const titleRef = useFocusOnMount<HTMLHeadingElement>()

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col gap-5 px-4 py-6">
      <h1
        ref={titleRef}
        tabIndex={-1}
        className="text-2xl font-bold text-brand-900 focus:outline-none"
      >
        {t('capture.preview.title')}
      </h1>
      <img
        src={url}
        alt={t('capture.preview.alt')}
        className="w-full rounded-xl border border-line object-contain"
      />
      <div className="mt-auto flex flex-col gap-3 pt-2">
        <button
          type="button"
          onClick={onContinue}
          className={`${BUTTON} bg-brand-600 text-surface focus-visible:outline-brand-900`}
        >
          {t('capture.preview.continue')}
        </button>
        <button type="button" onClick={onRetake} className={SECONDARY_WIDE}>
          {t('capture.preview.retake')}
        </button>
      </div>
    </main>
  )
}

/** Contenu de l'écran, monté seulement après le consentement : aucune demande de
 *  géolocalisation avant. */
function CaptureScreen() {
  const { t } = useTranslation()
  const titleRef = useFocusOnMount<HTMLHeadingElement>()
  const reasonId = useId()
  const ruleId = useId()
  const { position, retry: retryPosition } = usePosition()
  const { config, retry: retryConfig } = usePublicConfig()
  const [continuedAnyway, setContinuedAnyway] = useState(false)
  const [photo, setPhoto] = useState<PhotoState>({ stage: 'none' })
  const inputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()
  const previewUrl = photo.stage === 'preview' ? photo.url : undefined

  // Adresse locale de l'aperçu libérée quand elle change ou quand l'écran est quitté.
  useEffect(() => {
    if (!previewUrl) return
    return () => URL.revokeObjectURL(previewUrl)
  }, [previewUrl])

  const verdict = assessCapture(position, config, continuedAnyway)
  const ready = canTakePhoto(verdict)
  // « Continuer quand même » vaut pour la Position en cours : hors Zone ou après une
  // erreur, une nouvelle Position imprécise redemande de patienter. Mise à jour pendant
  // le rendu (état dérivé), sans effet.
  if (continuedAnyway && !keepsContinuation(verdict)) setContinuedAnyway(false)

  function retryPositionAgain() {
    setContinuedAnyway(false)
    retryPosition()
  }

  function retryConfigAgain() {
    setContinuedAnyway(false)
    retryConfig()
  }

  async function onPhotoChosen(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    // Le même fichier pourra être choisi à nouveau après « Reprendre la photo ».
    event.target.value = ''
    if (!file || position.status !== 'located') return
    // Position, précision et horodatage de l'appareil au moment de la prise de vue.
    const at = { lat: position.lat, lng: position.lng, accuracy: position.accuracy }
    const capturedAt = new Date().toISOString()
    setPhoto({ stage: 'processing' })
    try {
      const jpeg = await preparePhoto(file, browserCodec)
      setPhoto({
        stage: 'preview',
        draft: { clientUuid: crypto.randomUUID(), photo: jpeg, ...at, capturedAt },
        url: URL.createObjectURL(jpeg),
      })
    } catch {
      // Rien n'est gardé : le Citoyen reprend la photo.
      setPhoto({ stage: 'unreadable' })
    }
  }

  if (photo.stage === 'preview') {
    return (
      <PhotoPreview
        url={photo.url}
        onRetake={() => setPhoto({ stage: 'none' })}
        onContinue={() => {
          setDraft(photo.draft)
          void navigate(PATHS.details)
        }}
      />
    )
  }

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col gap-5 px-4 py-6">
      <h1
        ref={titleRef}
        tabIndex={-1}
        className="text-2xl font-bold text-brand-900 focus:outline-none"
      >
        {t('capture.title')}
      </h1>

      {/* Région annoncée : une phrase courte par type d'état, lue seulement quand l'état
          change (pas à chaque mesure GPS : la précision est affichée hors de la région). */}
      <p role="status" className="sr-only">
        {t(ANNOUNCEMENTS[verdict.kind])}
      </p>
      <section
        aria-labelledby={ruleId}
        className="flex gap-3 rounded-xl border-2 border-danger bg-surface p-4"
      >
        <NoPersonIcon className="size-8 shrink-0 stroke-danger" />
        <div className="flex flex-col gap-1">
          <h2 id={ruleId} className="text-lg font-bold text-ink">
            {t('capture.rule.title')}
          </h2>
          <p className="text-ink">{t('capture.rule.body')}</p>
        </div>
      </section>

      <div className="flex flex-col gap-3">
        <Status
          textId={reasonId}
          verdict={verdict}
          position={position}
          onRetryPosition={retryPositionAgain}
          onRetryConfig={retryConfigAgain}
          onContinue={() => setContinuedAnyway(true)}
        />
      </div>

      <div className="mt-auto flex flex-col gap-3 pt-2">
        {photo.stage === 'processing' && (
          <p role="status" className="text-ink">
            {t('capture.photo.processing')}
          </p>
        )}
        {photo.stage === 'unreadable' && (
          <p role="alert" className="flex gap-2 text-ink">
            <AlertIcon className="size-6 shrink-0 stroke-danger" />
            <span>{t('capture.photo.unreadable')}</span>
          </p>
        )}
        {/* Prise de vue directe, appareil photo arrière ; le bouton visible l'ouvre. */}
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          capture="environment"
          tabIndex={-1}
          aria-hidden="true"
          className="hidden"
          data-testid="camera-input"
          onChange={(event) => void onPhotoChosen(event)}
        />
        <button
          type="button"
          disabled={!ready || photo.stage === 'processing'}
          aria-describedby={ready ? undefined : reasonId}
          onClick={() => inputRef.current?.click()}
          className={`${BUTTON} flex items-center justify-center gap-3 bg-brand-600 text-surface focus-visible:outline-brand-900 disabled:cursor-not-allowed disabled:bg-mint disabled:text-muted`}
        >
          <CameraIcon className="size-6 shrink-0" />
          {t('capture.trigger')}
        </button>
        <Link
          to={PATHS.home}
          className="inline-flex min-h-11 items-center self-center rounded-lg px-4 font-semibold text-brand-600 underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-900"
        >
          {t('capture.back')}
        </Link>
      </div>
    </main>
  )
}

/** Écran 2 · Capture. Un lien direct sans consentement à jour renvoie vers le consentement. */
export function CapturePage() {
  const accepted = useCurrentConsent()
  if (accepted === undefined) return null
  if (!accepted) return <Navigate to={PATHS.consent} replace />
  return <CaptureScreen />
}
