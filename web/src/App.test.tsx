// Routage et rendu de la coquille, sans bibliothèque DOM : matchRoutes et renderToString.
import type { ReactElement } from 'react'
import { renderToString } from 'react-dom/server'
import { MemoryRouter, matchRoutes } from 'react-router'
import { describe, expect, it } from 'vitest'

import { routes } from './routes.tsx'
import { ConsentPage } from './features/consent/ConsentPage.tsx'
import { HomePage } from './features/home/HomePage.tsx'
import { NotFoundPage } from './features/not-found/NotFoundPage.tsx'
import { CapturePage } from './features/report/CapturePage.tsx'
import { ReportEntry } from './features/report/ReportEntry.tsx'
import fr from './i18n/fr.json'
import i18n from './i18n/index.ts'

function matchedComponent(path: string): unknown {
  const matches = matchRoutes(routes, path)
  const element = matches?.at(-1)?.route.element as ReactElement | undefined
  return element?.type
}

function render(page: ReactElement): string {
  return renderToString(<MemoryRouter>{page}</MemoryRouter>)
}

// renderToString échappe le texte (l'apostrophe devient &#x27;) : on compare au texte échappé.
function escaped(text: string): string {
  return text
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#x27;')
}

describe('routes', () => {
  it('/ affiche l’accueil', () => {
    expect(matchedComponent('/')).toBe(HomePage)
  })

  it('le parcours de signalement a ses trois routes', () => {
    expect(matchedComponent('/signaler')).toBe(ReportEntry)
    expect(matchedComponent('/signaler/consentement')).toBe(ConsentPage)
    expect(matchedComponent('/signaler/capture')).toBe(CapturePage)
  })

  it('une route inconnue affiche la page introuvable', () => {
    expect(matchedComponent('/n-importe-quoi')).toBe(NotFoundPage)
    expect(matchedComponent('/un/chemin/profond')).toBe(NotFoundPage)
  })
})

describe('rendu en français', () => {
  it('i18n démarre en fr', () => {
    expect(i18n.language).toBe('fr')
  })

  it('l’accueil affiche le nom, l’accroche et le bouton « Signaler un dépôt » vers /signaler', () => {
    const html = render(<HomePage />)
    expect(html).toMatch(new RegExp(`<h1[^>]*>${escaped(fr.app.name)}</h1>`))
    expect(html).toContain(escaped(fr.home.tagline))
    expect(html).toMatch(/<a [^>]*href="\/signaler"/)
    expect(html).toContain(escaped(fr.home.report))
    expect(html).toContain(escaped(fr.home.reportHint))
    // Pictogramme décoratif : le libellé visible suffit.
    expect(html).toMatch(/<svg [^>]*aria-hidden="true"/)
  })

  it('le consentement présente chaque point, la case non cochée et les deux boutons', () => {
    const html = render(<ConsentPage />)
    for (const text of [
      fr.consent.title,
      fr.consent.location.title,
      fr.consent.location.body,
      fr.consent.photo.title,
      fr.consent.photo.body,
      fr.consent.people.title,
      fr.consent.people.body,
      fr.consent.device.title,
      fr.consent.device.body,
      fr.consent.reinstall,
      fr.consent.training.label,
      fr.consent.training.hint,
      fr.consent.accept,
      fr.consent.decline,
    ]) {
      expect(html).toContain(escaped(text))
    }
    const checkbox = html.match(/<input [^>]*type="checkbox"[^>]*>/)?.[0] ?? ''
    expect(checkbox).not.toBe('')
    expect(checkbox).not.toMatch(/\bchecked\b/)
    expect(html).not.toContain(escaped(fr.consent.saveError))
  })

  it('la capture n’affiche rien avant d’avoir lu le consentement', () => {
    expect(render(<CapturePage />)).toBe('')
    expect(render(<ReportEntry />)).toBe('')
  })

  it('la page introuvable affiche son titre et un lien vers /', () => {
    const html = render(<NotFoundPage />)
    expect(html).toContain(escaped(fr.notFound.title))
    expect(html).toMatch(new RegExp(`<a [^>]*href="/"[^>]*>${escaped(fr.notFound.back)}</a>`))
  })
})
