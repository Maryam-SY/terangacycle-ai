import { useTranslation } from 'react-i18next'
import { Navigate, useNavigate } from 'react-router'

import { PATHS } from '../../paths.ts'
import { CameraIcon, CheckIcon, FlagIcon, ShieldCheckIcon, TruckIcon } from '../../ui/icons.tsx'
import { useFocusOnMount } from '../../ui/useFocusOnMount.ts'
import { clearDraft, clearLastReport, getLastReport } from './draft.ts'

// Écran 4 · Confirmation (story 1.13) : remerciement, Numéro de suivi, Frise de suivi à
// l'étape « Signalé », étiquette « Données de démonstration » si besoin, retour à
// l'accueil (brouillon effacé).

const STEPS = [
  { key: 'reported', Icon: FlagIcon },
  { key: 'validated', Icon: ShieldCheckIcon },
  { key: 'assigned', Icon: TruckIcon },
  { key: 'collected', Icon: CameraIcon },
] as const

/** Frise de suivi en 4 étapes ; l'étape courante est marquée par une coche et un libellé. */
export function TrackingTimeline({ current }: { current: (typeof STEPS)[number]['key'] }) {
  const { t } = useTranslation()
  return (
    <ol className="flex flex-col gap-3" aria-label={t('confirmation.timeline')}>
      {STEPS.map(({ key, Icon }) => {
        const isCurrent = key === current
        return (
          <li
            key={key}
            aria-current={isCurrent ? 'step' : undefined}
            className={`flex items-center gap-3 rounded-xl border-2 p-3 ${
              isCurrent ? 'border-brand-600 bg-mint font-bold text-ink' : 'border-line text-muted'
            }`}
          >
            <Icon className={`size-6 shrink-0 ${isCurrent ? 'text-brand-600' : 'text-muted'}`} />
            <span className="flex-1">{t(`confirmation.steps.${key}`)}</span>
            {isCurrent && (
              <span className="flex items-center gap-1 text-sm text-brand-600">
                <CheckIcon className="size-5" />
                {t('confirmation.current')}
              </span>
            )}
          </li>
        )
      })}
    </ol>
  )
}

export function ConfirmationPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const titleRef = useFocusOnMount<HTMLHeadingElement>()
  const report = getLastReport()
  if (report === null) return <Navigate to={PATHS.home} replace />

  function goHome() {
    clearDraft()
    clearLastReport()
    void navigate(PATHS.home, { replace: true })
  }

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="bg-brand-900 px-4 pt-10 pb-8">
        <div className="mx-auto flex max-w-md flex-col gap-3">
          {report.is_demo && (
            <span className="self-start rounded-full bg-accent px-3 py-1 text-sm font-bold text-ink">
              {t('demo.label')}
            </span>
          )}
          <h1 ref={titleRef} tabIndex={-1} className="text-3xl font-bold text-surface focus:outline-none">
            {t('confirmation.title')}
          </h1>
          <p className="text-mint">{t('confirmation.trackingLabel')}</p>
          <p className="font-mono text-2xl font-bold tracking-wide text-surface">
            {report.tracking_number}
          </p>
        </div>
      </header>
      <main className="mx-auto flex w-full max-w-md flex-1 flex-col gap-5 px-4 py-6">
        <TrackingTimeline current="reported" />
        <button
          type="button"
          onClick={goHome}
          className="mt-auto min-h-12 rounded-xl bg-brand-600 px-4 text-lg font-semibold text-surface focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-900"
        >
          {t('confirmation.home')}
        </button>
      </main>
    </div>
  )
}
