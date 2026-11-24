// Routage et rendu de la coquille, sans bibliothèque DOM : matchRoutes et renderToString.
import type { ReactElement } from 'react'
import { renderToString } from 'react-dom/server'
import { MemoryRouter, matchRoutes } from 'react-router'
import { describe, expect, it } from 'vitest'

import { routes } from './routes.tsx'
import { HomePage } from './features/home/HomePage.tsx'
import { NotFoundPage } from './features/not-found/NotFoundPage.tsx'
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

  it('une route inconnue affiche la page introuvable', () => {
    expect(matchedComponent('/n-importe-quoi')).toBe(NotFoundPage)
    expect(matchedComponent('/un/chemin/profond')).toBe(NotFoundPage)
  })
})

describe('rendu en français', () => {
  it('i18n démarre en fr', () => {
    expect(i18n.language).toBe('fr')
  })

  it('l’accueil affiche le titre et le sous-titre de fr.json', () => {
    const html = render(<HomePage />)
    expect(html).toContain(escaped(fr.home.title))
    expect(html).toContain(escaped(fr.home.subtitle))
  })

  it('la page introuvable affiche son titre et un lien vers /', () => {
    const html = render(<NotFoundPage />)
    expect(html).toContain(escaped(fr.notFound.title))
    expect(html).toMatch(new RegExp(`<a [^>]*href="/"[^>]*>${escaped(fr.notFound.back)}</a>`))
  })
})
