import { useTranslation } from 'react-i18next'
import { Link } from 'react-router'

export function NotFoundPage() {
  const { t } = useTranslation()

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col justify-center gap-4 px-4 py-8">
      <h1 className="text-2xl font-bold text-brand-900">{t('notFound.title')}</h1>
      <Link
        to="/"
        className="inline-flex min-h-11 items-center self-start rounded-lg bg-brand-600 px-4 font-semibold text-surface underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-900"
      >
        {t('notFound.back')}
      </Link>
    </main>
  )
}
