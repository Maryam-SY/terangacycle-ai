import { useId, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { Navigate, useLocation, useNavigate } from 'react-router'

import { clearDraft } from '../../offline/draft.ts'
import { PATHS } from '../../paths.ts'
import { InfoIcon } from '../../ui/icons.tsx'
import { useFocusOnMount } from '../../ui/useFocusOnMount.ts'
import { TrackingTimeline } from './TrackingTimeline.tsx'

// Écran 4 · Confirmation (maquette, nœud 1:97 ; story 1.13) : remerciement, Numéro de
// suivi, Frise de suivi à l'étape « Signalé », étiquette « Données de démonstration »
// [HORS MAQUETTE] pour un Signalement de démonstration. Les données arrivent par l'état
// de navigation de l'écran 3 ; un lien direct, sans état, ramène à l'accueil.
// Donnée personnelle : le Numéro de suivi est affiché, jamais écrit dans la console.

export interface ConfirmationState {
  trackingNumber: string
  isDemo: boolean
}

function parseState(value: unknown): ConfirmationState | undefined {
  if (value === null || typeof value !== 'object') return undefined
  const { trackingNumber, isDemo } = value as Record<string, unknown>
  if (typeof trackingNumber !== 'string' || trackingNumber === '') return undefined
  if (typeof isDemo !== 'boolean') return undefined
  return { trackingNumber, isDemo }
}

function ConfirmationScreen({ trackingNumber, isDemo }: ConfirmationState) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const titleRef = useFocusOnMount<HTMLHeadingElement>()
  const labelId = useId()
  const leaving = useRef(false)

  async function backHome() {
    if (leaving.current) return
    leaving.current = true
    // Déjà effacé après l'envoi : sans erreur s'il n'y a plus rien.
    await clearDraft().catch(() => undefined)
    void navigate(PATHS.home, { replace: true })
  }

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col gap-5 px-4 py-6">
      <h1
        ref={titleRef}
        tabIndex={-1}
        className="text-2xl font-bold text-brand-900 focus:outline-none"
      >
        {t('confirmation.title')}
      </h1>
      <p className="text-ink">{t('confirmation.body')}</p>

      {isDemo && (
        <div className="flex gap-3 rounded-xl border-2 border-warning-ink bg-warning-bg p-4 text-warning-ink">
          <InfoIcon className="size-6 shrink-0" />
          <div className="flex flex-col gap-1">
            <p className="font-bold">{t('confirmation.demo')}</p>
            <p>{t('confirmation.demoHint')}</p>
          </div>
        </div>
      )}

      <section
        aria-labelledby={labelId}
        className="flex flex-col items-center gap-1 rounded-xl bg-mint p-4 text-center"
      >
        <h2 id={labelId} className="text-base font-semibold text-brand-900">
          {t('confirmation.trackingLabel')}
        </h2>
        <p className="text-2xl font-bold tracking-wide break-all text-ink tabular-nums">
          {trackingNumber}
        </p>
      </section>

      <TrackingTimeline current="reported" />

      <div className="mt-auto flex flex-col gap-3 pt-2">
        <button
          type="button"
          onClick={() => void backHome()}
          className="min-h-12 rounded-xl bg-brand-600 px-4 text-lg font-semibold text-surface focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-900"
        >
          {t('confirmation.home')}
        </button>
      </div>
    </main>
  )
}

/** Écran 4. Sans état de navigation valide (lien direct, rechargement après fermeture) :
 *  retour à l'accueil. */
export function ConfirmationPage() {
  const location = useLocation()
  const state = parseState(location.state)
  if (!state) return <Navigate to={PATHS.home} replace />
  return <ConfirmationScreen {...state} />
}
