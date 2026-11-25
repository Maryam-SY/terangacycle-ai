import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, Navigate } from 'react-router'

import { getDraft, type Draft } from '../../offline/draft.ts'
import { PATHS } from '../../paths.ts'
import { InfoIcon, LocationIcon } from '../../ui/icons.tsx'
import { useFocusOnMount } from '../../ui/useFocusOnMount.ts'
import { useObjectUrl } from '../../ui/useObjectUrl.ts'
import { useCurrentConsent } from '../consent/useCurrentConsent.ts'
import { displayedAccuracy } from './capture.ts'

// Écran 3 · Détails, provisoire (story 1.9) : montre le brouillon gardé par la capture.
// La Taille de tas, le Type de déchet, le commentaire et l'envoi arrivent avec la
// story 1.13. Sans consentement à jour : le consentement. Sans brouillon (lien direct,
// brouillon illisible ou périmé) : retour à la capture.
// Donnée personnelle : la Position n'est jamais affichée, seulement sa précision.

function DetailsScreen({ draft }: { draft: Draft }) {
  const { t } = useTranslation()
  const titleRef = useFocusOnMount<HTMLHeadingElement>()
  const photoUrl = useObjectUrl(draft.photo)

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col gap-5 px-4 py-6">
      <h1
        ref={titleRef}
        tabIndex={-1}
        className="text-2xl font-bold text-brand-900 focus:outline-none"
      >
        {t('details.title')}
      </h1>
      {photoUrl && (
        <img
          src={photoUrl}
          alt={t('details.photoAlt')}
          className="max-h-[40dvh] w-full rounded-xl bg-mint object-contain"
        />
      )}
      <p className="flex gap-3 text-ink">
        <LocationIcon className="size-6 shrink-0 text-brand-600" />
        <span>{t('details.position', { accuracy: displayedAccuracy(draft.accuracy) })}</span>
      </p>
      <p className="flex gap-3 rounded-xl bg-mint p-4 text-ink">
        <InfoIcon className="size-6 shrink-0 text-brand-600" />
        <span>{t('details.soon')}</span>
      </p>
      <Link
        to={PATHS.capture}
        className="mt-auto inline-flex min-h-11 items-center self-center rounded-lg px-4 font-semibold text-brand-600 underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-900"
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
