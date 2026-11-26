import { useTranslation } from 'react-i18next'
import { Navigate } from 'react-router'

import { PATHS } from '../../paths.ts'
import { useFocusOnMount } from '../../ui/useFocusOnMount.ts'
import { getDraft } from './draft.ts'

// Écran 3 · Détails et envoi. Story 1.9 : seulement l'arrivée avec le brouillon (photo et
// Position) ; les champs et l'envoi arrivent avec la story 1.13. Sans brouillon (lien
// direct, rechargement), retour à la capture.
export function DetailsPage() {
  const { t } = useTranslation()
  const titleRef = useFocusOnMount<HTMLHeadingElement>()
  if (getDraft() === null) return <Navigate to={PATHS.capture} replace />

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col gap-5 px-4 py-6">
      <h1
        ref={titleRef}
        tabIndex={-1}
        className="text-2xl font-bold text-brand-900 focus:outline-none"
      >
        {t('details.title')}
      </h1>
    </main>
  )
}
