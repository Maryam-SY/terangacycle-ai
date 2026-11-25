import { useTranslation } from 'react-i18next'
import { Link } from 'react-router'

import { PATHS } from '../../paths.ts'
import { CameraIcon } from '../../ui/icons.tsx'
import { useFocusOnMount } from '../../ui/useFocusOnMount.ts'

// Écran 1 · Accueil (maquette, nœud 1:2) : en-tête vert foncé, grande carte-bouton
// « Signaler un dépôt ». Les entrées de rôle (story 2.3), « Mes Signalements » (1.13) et
// le bandeau démo (2.1) viendront s'ajouter sous la carte.
export function HomePage() {
  const { t } = useTranslation()
  const titleRef = useFocusOnMount<HTMLHeadingElement>()

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="bg-brand-900 px-4 pt-10 pb-8">
        <div className="mx-auto flex max-w-md flex-col gap-2">
          <h1
            ref={titleRef}
            tabIndex={-1}
            className="text-3xl font-bold text-surface focus:outline-none"
          >
            {t('app.name')}
          </h1>
          <p className="text-lg text-mint">{t('home.tagline')}</p>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-md flex-1 flex-col gap-4 px-4 py-6">
        <Link
          to={PATHS.report}
          className="flex min-h-11 items-center gap-4 rounded-2xl bg-brand-600 p-5 text-surface focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-900"
        >
          <span className="flex size-16 shrink-0 items-center justify-center rounded-full bg-brand-900 text-accent">
            <CameraIcon className="size-8" />
          </span>
          <span className="flex min-w-0 flex-col gap-1">
            <span className="text-xl font-bold">{t('home.report')}</span>
            <span className="text-base">{t('home.reportHint')}</span>
          </span>
        </Link>
      </main>
    </div>
  )
}
