import { useEffect, useId, useRef, useState, type ChangeEvent, type Ref } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, Navigate, useNavigate } from 'react-router'

import { sendReport, type HeapSize, type WasteType } from '../../api/reports.ts'
import { clearDraft, getDraft, type Draft } from '../../offline/draft.ts'
import { PATHS } from '../../paths.ts'
import { AlertIcon, LocationIcon, SendIcon } from '../../ui/icons.tsx'
import { useFocusOnMount } from '../../ui/useFocusOnMount.ts'
import { useObjectUrl } from '../../ui/useObjectUrl.ts'
import { WasteTypePicker } from '../classify/WasteTypePicker.tsx'
import { getConsent, hasCurrentConsent } from '../consent/consent.ts'
import { useCurrentConsent } from '../consent/useCurrentConsent.ts'
import { displayedAccuracy } from './capture.ts'
import type { ConfirmationState } from './ConfirmationPage.tsx'
import {
  buildMeta,
  codePointLength,
  COMMENT_MAX,
  limitComment,
  missingField,
  sendFailure,
  type SendFailure,
} from './details.ts'
import { HeapSizePicker } from './HeapSizePicker.tsx'

// Écran 3 · Résultat IA (maquette, nœud 1:57), adapté sans proposition IA (story 1.13) :
// miniature de la photo, Taille de tas (obligatoire), Type de déchet (facultatif),
// commentaire « n/280 », puis « Envoyer » (POST /v1/reports) et l'écran 4.
// Taille, Type et commentaire restent dans l'état de l'écran ; le brouillon (photo,
// Position, Identifiant client) reste dans Dexie jusqu'au succès de l'envoi : après une
// erreur, la saisie est gardée et le même Identifiant client repart.
// Sans consentement à jour : le consentement. Sans brouillon (lien direct, brouillon
// illisible ou périmé) : retour à la capture.
// Donnée personnelle : la Position n'est jamais affichée, seulement sa précision ; rien
// n'est écrit dans la console.

const BUTTON =
  'min-h-12 rounded-xl px-4 text-lg font-semibold focus-visible:outline-2 focus-visible:outline-offset-2'
const PRIMARY = `${BUTTON} flex items-center justify-center gap-3 bg-brand-600 text-surface focus-visible:outline-brand-900 disabled:cursor-not-allowed disabled:bg-mint disabled:text-muted`
const SECONDARY_LINK = `${BUTTON} inline-flex items-center self-start border-2 border-brand-600 bg-surface text-brand-600 focus-visible:outline-brand-900`

/** Erreur montrée sur l'écran (le consentement manquant, lui, change d'écran). */
type ShownFailure = Exclude<SendFailure, { kind: 'consent' }>

function Failure({
  failure,
  messageRef,
}: {
  failure: ShownFailure
  messageRef: Ref<HTMLParagraphElement>
}) {
  const { t } = useTranslation()
  return (
    <div className="flex gap-3 text-ink">
      <AlertIcon className="size-6 shrink-0 stroke-danger" />
      <div className="flex flex-col gap-3">
        <p ref={messageRef} tabIndex={-1} className="focus:outline-none">
          {t(failure.messageKey)}
        </p>
        {failure.kind === 'outside-zone' && (
          <Link to={PATHS.capture} className={SECONDARY_LINK}>
            {t('details.backToCapture')}
          </Link>
        )}
        {failure.kind === 'retake' && (
          <Link to={PATHS.capture} className={SECONDARY_LINK}>
            {t('details.retake')}
          </Link>
        )}
      </div>
    </div>
  )
}

/** Contenu de l'écran 3 pour un brouillon lu et valide. */
export function DetailsScreen({ draft }: { draft: Draft }) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const titleRef = useFocusOnMount<HTMLHeadingElement>()
  const photoUrl = useObjectUrl(draft.photo)
  const reasonId = useId()
  const commentId = useId()
  const commentHintId = useId()
  const counterId = useId()
  const [heapSize, setHeapSize] = useState<HeapSize>()
  const [wasteType, setWasteType] = useState<WasteType>()
  const [comment, setComment] = useState('')
  const [sending, setSending] = useState(false)
  const [failure, setFailure] = useState<ShownFailure>()
  // Garde contre un double appui : posée avant tout rendu, levée seulement après un échec.
  const sendingRef = useRef(false)
  // Faux dès que l'écran est quitté : un envoi encore en cours ne navigue plus.
  const onScreen = useRef(true)
  const failureRef = useRef<HTMLParagraphElement>(null)
  const focusFailure = useRef(false)

  useEffect(() => {
    onScreen.current = true
    return () => {
      onScreen.current = false
    }
  }, [])

  // Le message d'erreur est lu : le focus y est placé dès qu'il est rendu.
  useEffect(() => {
    if (!failure || !focusFailure.current) return
    focusFailure.current = false
    failureRef.current?.focus()
  }, [failure])

  const missing = missingField(draft, heapSize)
  const length = codePointLength(comment)

  function changeComment(event: ChangeEvent<HTMLTextAreaElement>) {
    setComment(limitComment(comment, event.target.value))
  }

  async function submit() {
    if (missing || !heapSize || sendingRef.current) return
    sendingRef.current = true
    setSending(true)
    setFailure(undefined)
    try {
      // Consentement lu au moment de l'envoi (il a pu être retiré entre-temps).
      const [terms, stored] = await Promise.all([hasCurrentConsent(), getConsent()])
      const meta = buildMeta(
        draft,
        { heapSize, wasteType, comment },
        { terms, training: stored?.training ?? false },
      )
      const { report } = await sendReport(meta, draft.photo)
      await clearDraft().catch(() => undefined)
      if (!onScreen.current) return
      const state: ConfirmationState = {
        trackingNumber: report.tracking_number,
        isDemo: report.is_demo,
      }
      void navigate(PATHS.confirmation, { replace: true, state })
    } catch (error) {
      sendingRef.current = false
      if (!onScreen.current) return
      const decided = sendFailure(error)
      if (decided.kind === 'consent') {
        void navigate(PATHS.consent, { replace: true })
        return
      }
      focusFailure.current = true
      setFailure(decided)
      setSending(false)
    }
  }

  let announcement: string
  if (sending) announcement = t('details.announce.sending')
  else if (failure) announcement = t('details.announce.error')
  else if (missing) announcement = t(`details.missing.${missing}`)
  else announcement = t('details.announce.ready')

  let sendLabel: string
  if (sending) sendLabel = t('details.sending')
  else if (failure?.kind === 'retry') sendLabel = t('details.retry')
  else sendLabel = t('details.send')

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col gap-5 px-4 py-6">
      <h1
        ref={titleRef}
        tabIndex={-1}
        className="text-2xl font-bold text-brand-900 focus:outline-none"
      >
        {t('details.title')}
      </h1>

      {/* Région annoncée : ce qui manque, l'envoi en cours, l'échec ou l'envoi possible. */}
      <p role="status" className="sr-only">
        {announcement}
      </p>

      {photoUrl && (
        <img
          src={photoUrl}
          alt={t('details.photoAlt')}
          className="max-h-[30dvh] w-full rounded-xl bg-mint object-contain"
        />
      )}
      <p className="flex gap-3 text-ink">
        <LocationIcon className="size-6 shrink-0 text-brand-600" />
        <span>{t('details.position', { accuracy: displayedAccuracy(draft.accuracy) })}</span>
      </p>

      <HeapSizePicker value={heapSize} onChange={setHeapSize} disabled={sending} />
      <WasteTypePicker value={wasteType} onChange={setWasteType} disabled={sending} />

      <div className="flex flex-col gap-2">
        <label htmlFor={commentId} className="text-lg font-semibold text-brand-900">
          {t('details.comment.label')}
        </label>
        <p id={commentHintId} className="text-sm text-muted">
          {t('details.comment.hint')}
        </p>
        <textarea
          id={commentId}
          value={comment}
          onChange={changeComment}
          disabled={sending}
          rows={3}
          aria-describedby={`${commentHintId} ${counterId}`}
          className="min-h-24 w-full rounded-xl border-2 border-muted bg-surface p-3 text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-900"
        />
        <p id={counterId} className="self-end text-sm text-muted">
          <span aria-hidden="true">{t('details.comment.counter', { length, max: COMMENT_MAX })}</span>
          <span className="sr-only">
            {t('details.comment.counterLabel', { length, max: COMMENT_MAX })}
          </span>
        </p>
      </div>

      <div className="mt-auto flex flex-col gap-3 pt-2">
        {failure && <Failure failure={failure} messageRef={failureRef} />}
        {missing && (
          <p id={reasonId} className="text-ink">
            {t(`details.missing.${missing}`)}
          </p>
        )}
        <button
          type="button"
          disabled={Boolean(missing) || sending}
          aria-describedby={missing ? reasonId : undefined}
          onClick={() => void submit()}
          className={`${PRIMARY} ${sending ? 'disabled:cursor-wait' : ''}`}
        >
          <SendIcon className="size-6 shrink-0" />
          {sendLabel}
        </button>
      </div>

      <Link
        to={PATHS.capture}
        className="inline-flex min-h-11 items-center self-center rounded-lg px-4 font-semibold text-brand-600 underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-900"
      >
        {t('details.back')}
      </Link>
    </main>
  )
}

/** Lecture du brouillon ; rien n'est rendu pendant la lecture. */
function DetailsLoader() {
  const [draft, setDraft] = useState<Draft | null>()

  useEffect(() => {
    let active = true
    void getDraft()
      .catch(() => undefined)
      .then((value) => {
        if (active) setDraft(value ?? null)
      })
    return () => {
      active = false
    }
  }, [])

  if (draft === undefined) return null
  if (draft === null) return <Navigate to={PATHS.capture} replace />
  return <DetailsScreen draft={draft} />
}

/** Écran 3. Un lien direct sans consentement à jour renvoie vers le consentement, comme la
 *  capture ; rien n'est rendu pendant la lecture. */
export function DetailsPage() {
  const accepted = useCurrentConsent()
  if (accepted === undefined) return null
  if (!accepted) return <Navigate to={PATHS.consent} replace />
  return <DetailsLoader />
}
