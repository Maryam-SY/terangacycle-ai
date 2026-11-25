import { useEffect, useId, useRef, useState, type ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router'

import { requestPersistentStorage } from '../../offline/db.ts'
import { PATHS } from '../../paths.ts'
import {
  AlertIcon,
  HeartIcon,
  InfoIcon,
  LocationIcon,
  NoPersonIcon,
  PhoneIcon,
  PhotoSendIcon,
} from '../../ui/icons.tsx'
import { useFocusOnMount } from '../../ui/useFocusOnMount.ts'
import { acceptConsent } from './consent.ts'

// Écran de consentement (FR-4) [HORS MAQUETTE], avant toute capture. Rien n'est demandé
// (géolocalisation, appareil photo) ni envoyé ici : le choix reste sur l'appareil.

function Topic({ icon, title, body }: { icon: ReactNode; title: string; body: string }) {
  const titleId = useId()
  return (
    <section aria-labelledby={titleId} className="flex gap-3 rounded-xl bg-mint p-4">
      <span className="shrink-0 text-brand-600">{icon}</span>
      <div className="flex flex-col gap-1">
        <h2 id={titleId} className="text-lg font-semibold text-brand-900">
          {title}
        </h2>
        <p className="text-ink">{body}</p>
      </div>
    </section>
  )
}

export function ConsentPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const hintId = useId()
  const [training, setTraining] = useState(false)
  const [saving, setSaving] = useState(false)
  const [failed, setFailed] = useState(false)
  const titleRef = useFocusOnMount<HTMLHeadingElement>()
  // Faux dès que l'écran est quitté (refus, démontage) : un enregistrement encore en cours
  // ne doit plus naviguer ni mettre à jour l'écran.
  const onScreen = useRef(true)

  useEffect(() => {
    onScreen.current = true
    return () => {
      onScreen.current = false
    }
  }, [])

  async function accept() {
    setSaving(true)
    setFailed(false)
    try {
      await acceptConsent({ training })
    } catch {
      if (onScreen.current) {
        setFailed(true)
        setSaving(false)
      }
      return
    }
    requestPersistentStorage()
    if (onScreen.current) void navigate(PATHS.capture, { replace: true })
  }

  function decline() {
    // Rien n'est mémorisé : le consentement sera redemandé au prochain signalement.
    onScreen.current = false
    void navigate(PATHS.home, { replace: true })
  }

  const button =
    'min-h-12 rounded-xl px-4 text-lg font-semibold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-900'

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col gap-5 px-4 py-6">
      <h1
        ref={titleRef}
        tabIndex={-1}
        className="text-2xl font-bold text-brand-900 focus:outline-none"
      >
        {t('consent.title')}
      </h1>
      <p className="text-ink">{t('consent.intro')}</p>

      <Topic
        icon={<LocationIcon />}
        title={t('consent.location.title')}
        body={t('consent.location.body')}
      />
      <Topic
        icon={<PhotoSendIcon />}
        title={t('consent.photo.title')}
        body={t('consent.photo.body')}
      />
      <Topic
        icon={<NoPersonIcon />}
        title={t('consent.people.title')}
        body={t('consent.people.body')}
      />
      <Topic
        icon={<PhoneIcon />}
        title={t('consent.device.title')}
        body={t('consent.device.body')}
      />

      <div className="flex gap-3 rounded-xl bg-warning-bg p-4 text-warning-ink">
        <InfoIcon className="size-6 shrink-0" />
        <p>{t('consent.reinstall')}</p>
      </div>

      <div className="flex flex-col gap-1 rounded-xl border border-line p-4">
        <label className="flex min-h-11 cursor-pointer items-start gap-3 text-ink">
          <input
            type="checkbox"
            checked={training}
            onChange={(event) => setTraining(event.target.checked)}
            aria-describedby={hintId}
            className="mt-0.5 size-6 shrink-0 cursor-pointer accent-brand-600"
          />
          <span className="flex gap-2">
            <span>{t('consent.training.label')}</span>
            <HeartIcon className="size-6 shrink-0 text-brand-600" />
          </span>
        </label>
        <p id={hintId} className="pl-9 text-sm text-muted">
          {t('consent.training.hint')}
        </p>
      </div>

      {failed && (
        <p role="alert" className="flex gap-2 text-ink">
          <AlertIcon className="size-6 shrink-0 stroke-danger" />
          <span>{t('consent.saveError')}</span>
        </p>
      )}

      <div className="mt-auto flex flex-col gap-3 pt-2">
        <button
          type="button"
          onClick={() => void accept()}
          disabled={saving}
          className={`${button} bg-brand-600 text-surface disabled:cursor-wait`}
        >
          {t('consent.accept')}
        </button>
        <button
          type="button"
          onClick={decline}
          disabled={saving}
          className={`${button} border-2 border-brand-600 bg-surface text-brand-600 disabled:cursor-wait`}
        >
          {t('consent.decline')}
        </button>
      </div>
    </main>
  )
}
