import { useTranslation } from 'react-i18next'

export function HomePage() {
  const { t } = useTranslation()

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col justify-center gap-3 px-4 py-8">
      <p className="text-sm font-semibold text-brand-600">{t('app.name')}</p>
      <h1 className="text-3xl font-bold text-brand-900">{t('home.title')}</h1>
      <p className="text-base text-muted">{t('home.subtitle')}</p>
    </main>
  )
}
