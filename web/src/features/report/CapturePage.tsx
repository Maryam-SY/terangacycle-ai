import { useTranslation } from 'react-i18next'
import { Link, Navigate } from 'react-router'

import { PATHS } from '../../paths.ts'
import { useFocusOnMount } from '../../ui/useFocusOnMount.ts'
import { useCurrentConsent } from '../consent/useCurrentConsent.ts'

/** Écran 2 · Capture, provisoire : la story 1.8 y ajoutera la Position et la photo.
 *  Un lien direct sans consentement à jour renvoie vers le consentement. */
export function CapturePage() {
  const { t } = useTranslation()
  const accepted = useCurrentConsent()
  const titleRef = useFocusOnMount<HTMLHeadingElement>()

  if (accepted === undefined) return null
  if (!accepted) return <Navigate to={PATHS.consent} replace />

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col justify-center gap-4 px-4 py-8">
      <h1
        ref={titleRef}
        tabIndex={-1}
        className="text-2xl font-bold text-brand-900 focus:outline-none"
      >
        {t('capture.title')}
      </h1>
      <p className="text-ink">{t('capture.soon')}</p>
      <Link
        to={PATHS.home}
        className="inline-flex min-h-11 items-center self-start rounded-lg bg-brand-600 px-4 font-semibold text-surface underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-900"
      >
        {t('capture.back')}
      </Link>
    </main>
  )
}
