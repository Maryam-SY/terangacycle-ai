import { useTranslation } from 'react-i18next'
import { Outlet } from 'react-router'

import { usePublicConfig } from '../features/report/usePublicConfig.ts'

// Mise en page commune à tous les écrans (story 2.1) : bandeau « Mode démonstration »
// en haut, sans bouton de fermeture, tant que `GET /v1/config` dit `demo_mode = true`.
// Hors ligne, le bandeau suit la dernière configuration gardée dans Dexie `meta`.

export function DemoBanner() {
  const { t } = useTranslation()
  const { config } = usePublicConfig()
  if (config.status !== 'ready' || !config.config.demo_mode) return null
  return (
    <section
      aria-label={t('demo.banner')}
      className="bg-accent px-4 py-2 text-center font-bold text-ink"
    >
      {t('demo.banner')}
    </section>
  )
}

export function AppLayout() {
  return (
    <>
      <DemoBanner />
      <Outlet />
    </>
  )
}
