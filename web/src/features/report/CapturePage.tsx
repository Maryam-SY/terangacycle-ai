import {
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
  type ChangeEvent,
  type ReactNode,
} from 'react'
import { useTranslation } from 'react-i18next'
import { Link, Navigate, useNavigate } from 'react-router'

import { clearDraft, saveDraft } from '../../offline/draft.ts'
import { PATHS } from '../../paths.ts'
import { AlertIcon, CameraIcon, InfoIcon, LocationIcon, NoPersonIcon } from '../../ui/icons.tsx'
import { useFocusOnMount } from '../../ui/useFocusOnMount.ts'
import { useObjectUrl } from '../../ui/useObjectUrl.ts'
import { useCurrentConsent } from '../consent/useCurrentConsent.ts'
import {
  assessCapture,
  canTakePhoto,
  keepsContinuation,
  type CaptureVerdict,
} from './capture.ts'
import {
  captureTime,
  MAX_PHOTO_FIX_AGE_MS,
  processPhoto,
  StalePhotoError,
  type ProcessedPhoto,
} from './photo.ts'
import { usePosition, type PositionState } from './usePosition.ts'
import { usePublicConfig } from './usePublicConfig.ts'

// Écran 2 · Capture : Position suivie en haute précision, Zone active vérifiée sur
// l'appareil, déclencheur « Prendre la photo » actif seulement si la Position est
// utilisable (story 1.8). Le déclencheur ouvre l'appareil photo arrière (prise de vue
// directe) ; la photo est allégée et nettoyée sur l'appareil, montrée en aperçu, puis
// gardée en brouillon avec sa Position (story 1.9).
// Donnée personnelle : ni coordonnée ni octet de photo dans la console ; rien n'est envoyé.

const BUTTON =
  'min-h-12 rounded-xl px-4 text-lg font-semibold focus-visible:outline-2 focus-visible:outline-offset-2'
const SECONDARY = `${BUTTON} self-start border-2 border-brand-600 bg-surface text-brand-600 focus-visible:outline-brand-900`
const PRIMARY = `${BUTTON} flex items-center justify-center gap-3 bg-brand-600 text-surface focus-visible:outline-brand-900 disabled:cursor-not-allowed disabled:bg-mint disabled:text-muted`

/** Annonce des lecteurs d'écran, une par type d'état. */
const ANNOUNCEMENTS = {
  waiting: 'capture.announce.waiting',
  'position-error': 'capture.announce.positionError',
  'config-unavailable': 'capture.announce.configUnavailable',
  'outside-zone': 'capture.announce.outsideZone',
  imprecise: 'capture.announce.imprecise',
  ready: 'capture.announce.ready',
} as const satisfies Record<CaptureVerdict['kind'], string>

/** Position gardée avec la photo : la dernière mesure au moment où le fichier arrive. */
interface Fix {
  lat: number
  lng: number
  accuracy: number
}

type PhotoState =
  | { stage: 'idle' }
  | { stage: 'processing' }
  | { stage: 'error'; reason: keyof typeof PHOTO_ERRORS }
  | {
      stage: 'preview'
      photo: ProcessedPhoto
      fix: Fix
      /** Heure de la prise (appareil), ISO 8601 : voir `captureTime`. */
      capturedAt: string
      saving: boolean
      saveFailed: boolean
    }

/** Photo refusée : illisible, trop ancienne, ou Position plus vérifiée (ou trop ancienne)
 *  à son arrivée. */
type FocusTarget = 'trigger' | 'preview' | 'processing' | 'error' | 'saveError'

const PHOTO_ERRORS = {
  unreadable: 'capture.photo.unreadable',
  stale: 'capture.photo.stale',
  position: 'capture.photo.position',
} as const

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

/** Consigne montrée à chaque capture, reprise comprise. */
function Rule() {
  const { t } = useTranslation()
  const titleId = useId()
  return (
    <section aria-labelledby={titleId} className="flex gap-3 rounded-xl bg-mint p-4">
      <NoPersonIcon className="size-6 shrink-0 text-brand-600" />
      <div className="flex flex-col gap-1">
        <h2 id={titleId} className="text-lg font-semibold text-brand-900">
          {t('capture.rule.title')}
        </h2>
        <p className="text-ink">{t('capture.rule.body')}</p>
      </div>
    </section>
  )
}

/** Contenu de l'écran, monté seulement après le consentement : aucune demande de
 *  géolocalisation avant. */
function CaptureScreen() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const focusTitle = useFocusOnMount<HTMLHeadingElement>()
  const headingRef = useRef<HTMLHeadingElement | null>(null)
  const titleRef = useCallback(
    (element: HTMLHeadingElement | null) => {
      headingRef.current = element
      focusTitle(element)
    },
    [focusTitle],
  )
  const reasonId = useId()
  const { position, retry: retryPosition } = usePosition()
  const { config, retry: retryConfig } = usePublicConfig()
  const [continuedAnyway, setContinuedAnyway] = useState(false)
  const [photo, setPhoto] = useState<PhotoState>({ stage: 'idle' })
  const inputRef = useRef<HTMLInputElement>(null)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const previewRef = useRef<HTMLImageElement>(null)
  const processingRef = useRef<HTMLParagraphElement>(null)
  const errorRef = useRef<HTMLParagraphElement>(null)
  const saveErrorRef = useRef<HTMLParagraphElement>(null)
  // Élément à focaliser dès qu'il est rendu : le bouton cliqué disparaît ou se désactive
  // (le focus tomberait sur <body>), et un message d'erreur doit être lu.
  const pendingFocus = useRef<FocusTarget | undefined>(undefined)
  // Numéro de la dernière photo reçue : un traitement dépassé (nouvelle photo, reprise,
  // écran quitté) ne met plus l'écran à jour.
  const attempt = useRef(0)
  const previewUrl = useObjectUrl(photo.stage === 'preview' ? photo.photo.blob : undefined)

  const verdict = assessCapture(position, config, continuedAnyway)
  const ready = canTakePhoto(verdict)
  const shooting = photo.stage === 'idle' || photo.stage === 'error'
  // « Continuer quand même » vaut pour la Position en cours : hors Zone ou après une
  // erreur, une nouvelle Position imprécise redemande de patienter. Mise à jour pendant
  // le rendu (état dérivé), sans effet.
  if (continuedAnyway && !keepsContinuation(verdict)) setContinuedAnyway(false)

  useEffect(
    () => () => {
      attempt.current += 1
    },
    [],
  )

  useEffect(() => {
    const target = pendingFocus.current
    if (!target) return
    let element: HTMLElement | null
    if (target === 'trigger') {
      // Déclencheur désactivé (Position perdue entre-temps) : le titre de l'écran.
      const trigger = triggerRef.current
      element = trigger && !trigger.disabled ? trigger : headingRef.current
    } else {
      const refs = {
        preview: previewRef,
        processing: processingRef,
        error: errorRef,
        saveError: saveErrorRef,
      }
      element = refs[target].current
    }
    // L'aperçu n'est rendu qu'une fois son URL créée : nouvel essai au rendu suivant.
    if (!element) return
    pendingFocus.current = undefined
    element.focus()
  }, [photo, previewUrl])

  function retryPositionAgain() {
    setContinuedAnyway(false)
    retryPosition()
  }

  function retryConfigAgain() {
    setContinuedAnyway(false)
    retryConfig()
  }

  async function receivePhoto(event: ChangeEvent<HTMLInputElement>) {
    const input = event.currentTarget
    const file = input.files?.[0]
    // Vidé : la même photo choisie à nouveau déclenche encore `change`.
    input.value = ''
    if (!file) return
    const now = Date.now()
    attempt.current += 1
    const current = attempt.current
    // Une nouvelle photo remplace l'ancien brouillon, qu'elle soit gardée ou non.
    void clearDraft().catch(() => undefined)
    // Position revérifiée à l'arrivée du fichier : elle a pu changer pendant la prise de
    // vue. Hors Zone ou perdue : refus. Devenue imprécise (fréquent quand le navigateur
    // passe en arrière-plan) : acceptée, sa précision est gardée avec la photo.
    // La mesure doit aussi être récente : le suivi s'arrête souvent pendant que
    // l'appareil photo est ouvert, et la Position gardée doit être celle de la prise.
    const usable = verdict.kind === 'ready' || verdict.kind === 'imprecise'
    if (
      !usable ||
      position.status !== 'located' ||
      now - position.fixedAt > MAX_PHOTO_FIX_AGE_MS
    ) {
      pendingFocus.current = 'error'
      setPhoto({ stage: 'error', reason: 'position' })
      return
    }
    const fix: Fix = { lat: position.lat, lng: position.lng, accuracy: position.accuracy }
    pendingFocus.current = 'processing'
    setPhoto({ stage: 'processing' })
    try {
      const processed = await processPhoto(file, now)
      if (attempt.current !== current) return
      pendingFocus.current = 'preview'
      setPhoto({
        stage: 'preview',
        photo: processed,
        fix,
        capturedAt: new Date(captureTime(file.lastModified, now)).toISOString(),
        saving: false,
        saveFailed: false,
      })
    } catch (error) {
      if (attempt.current !== current) return
      pendingFocus.current = 'error'
      setPhoto({ stage: 'error', reason: error instanceof StalePhotoError ? 'stale' : 'unreadable' })
    }
  }

  function retake() {
    attempt.current += 1
    pendingFocus.current = 'trigger'
    setPhoto({ stage: 'idle' })
  }

  async function keepPhoto() {
    if (photo.stage !== 'preview' || photo.saving) return
    const current = attempt.current
    setPhoto({ ...photo, saving: true, saveFailed: false })
    try {
      await saveDraft({ photo: photo.photo.blob, ...photo.fix, capturedAt: photo.capturedAt })
    } catch {
      if (attempt.current === current) {
        pendingFocus.current = 'saveError'
        setPhoto({ ...photo, saving: false, saveFailed: true })
      }
      return
    }
    if (attempt.current === current) void navigate(PATHS.details)
  }

  let announcement: string
  if (photo.stage === 'processing') announcement = t('capture.announce.processing')
  else if (photo.stage === 'preview') announcement = t('capture.announce.preview')
  else if (photo.stage === 'error') announcement = t('capture.announce.photoError')
  else announcement = t(ANNOUNCEMENTS[verdict.kind])

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
        {announcement}
      </p>

      {photo.stage === 'preview' ? (
        <>
          {previewUrl && (
            <img
              ref={previewRef}
              tabIndex={-1}
              src={previewUrl}
              alt={t('capture.photo.alt')}
              width={photo.photo.width}
              height={photo.photo.height}
              className="max-h-[60dvh] w-full rounded-xl bg-mint object-contain focus:outline-none"
            />
          )}
          <div className="mt-auto flex flex-col gap-3 pt-2">
            {photo.saveFailed && (
              <Message icon={<AlertIcon className="size-6 shrink-0 stroke-danger" />}>
                <p ref={saveErrorRef} tabIndex={-1} className="focus:outline-none">
                  {t('capture.photo.saveError')}
                </p>
              </Message>
            )}
            <button
              type="button"
              disabled={photo.saving}
              onClick={() => void keepPhoto()}
              className={`${PRIMARY} disabled:cursor-wait`}
            >
              {t('capture.photo.continue')}
            </button>
            <button
              type="button"
              disabled={photo.saving}
              onClick={retake}
              className={`${SECONDARY} flex items-center justify-center gap-3 self-stretch disabled:cursor-wait`}
            >
              <CameraIcon className="size-6 shrink-0" />
              {t('capture.photo.retake')}
            </button>
          </div>
        </>
      ) : (
        <>
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
            <Rule />
            {photo.stage === 'processing' && (
              <Message icon={<CameraIcon className="size-6 shrink-0 text-brand-600" />}>
                <p ref={processingRef} tabIndex={-1} className="focus:outline-none">
                  {t('capture.photo.processing')}
                </p>
              </Message>
            )}
            {photo.stage === 'error' && (
              <Message icon={<AlertIcon className="size-6 shrink-0 stroke-danger" />}>
                <p ref={errorRef} tabIndex={-1} className="focus:outline-none">
                  {t(PHOTO_ERRORS[photo.reason])}
                </p>
              </Message>
            )}
            {/* Prise de vue directe : l'appareil photo arrière du téléphone, sans viseur
                dans la page. Là où `capture` est ignoré (ordinateur), l'ancienneté du
                fichier écarte une photo de la galerie. Champ caché, atteint seulement par
                le déclencheur ; il n'est pas désactivé selon la Position, pour ne pas
                perdre une photo si la mesure change pendant la prise de vue. */}
            <input
              ref={inputRef}
              type="file"
              accept="image/*"
              capture="environment"
              disabled={!shooting}
              tabIndex={-1}
              onChange={(event) => void receivePhoto(event)}
              className="hidden"
            />
            <button
              ref={triggerRef}
              type="button"
              disabled={!ready || !shooting}
              aria-describedby={ready ? undefined : reasonId}
              onClick={() => inputRef.current?.click()}
              className={PRIMARY}
            >
              <CameraIcon className="size-6 shrink-0" />
              {t('capture.trigger')}
            </button>
          </div>
        </>
      )}

      <Link
        to={PATHS.home}
        className="inline-flex min-h-11 items-center self-center rounded-lg px-4 font-semibold text-brand-600 underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-900"
      >
        {t('capture.back')}
      </Link>
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
