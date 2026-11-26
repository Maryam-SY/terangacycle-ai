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
import { ConfirmationPage } from './features/report/ConfirmationPage.tsx'
import { DetailsPage, DetailsScreen } from './features/report/DetailsPage.tsx'
import { ReportEntry } from './features/report/ReportEntry.tsx'
import { TrackingTimeline } from './features/report/TrackingTimeline.tsx'
import { WasteTypeBadge, WasteTypePicker } from './features/classify/WasteTypePicker.tsx'
import { WASTE_TYPES } from './features/classify/wasteTypes.ts'
import fr from './i18n/fr.json'
import i18n from './i18n/index.ts'
import type { Draft } from './offline/draft.ts'

function matchedComponent(path: string): unknown {
  const matches = matchRoutes(routes, path)
  const element = matches?.at(-1)?.route.element as ReactElement | undefined
  return element?.type
}

function render(page: ReactElement, state?: unknown): string {
  const entry = { pathname: '/', state }
  return renderToString(<MemoryRouter initialEntries={[entry]}>{page}</MemoryRouter>)
}

const DRAFT: Draft = {
  photo: new Blob([new Uint8Array([0xff, 0xd8, 0xff, 0xd9])], { type: 'image/jpeg' }),
  lat: 14.6708,
  lng: -17.4381,
  accuracy: 8.2,
  capturedAt: '2026-11-26T10:00:00.000Z',
  clientUuid: '0b8f3c52-7a4e-4f1d-9c3b-2e6a1d5f8a90',
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

  it('le parcours de signalement a ses cinq routes', () => {
    expect(matchedComponent('/signaler')).toBe(ReportEntry)
    expect(matchedComponent('/signaler/consentement')).toBe(ConsentPage)
    expect(matchedComponent('/signaler/capture')).toBe(CapturePage)
    expect(matchedComponent('/signaler/details')).toBe(DetailsPage)
    expect(matchedComponent('/signaler/confirmation')).toBe(ConfirmationPage)
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

  it('l’écran 3 n’affiche rien avant d’avoir lu le brouillon', () => {
    expect(render(<DetailsPage />)).toBe('')
  })

  it('écran 3 : position, Taille et Type sans présélection, « Envoyer » désactivé avec sa raison', () => {
    const html = render(<DetailsScreen draft={DRAFT} />)
    expect(html).toContain(escaped(fr.details.title))
    expect(html).toContain(escaped(fr.details.position.replace('{{accuracy}}', '9')))
    // Le texte provisoire de la story 1.9 a disparu.
    expect(fr.details).not.toHaveProperty('soon')
    for (const text of [
      fr.heapSize.legend,
      fr.heapSize.small,
      fr.heapSize.medium,
      fr.heapSize.large,
      fr.wasteType.legend,
      fr.wasteType.hint,
      fr.wasteType.plastic,
      fr.wasteType.metal,
      fr.wasteType.glass,
      fr.wasteType.organic,
      fr.wasteType.mixed,
      fr.details.comment.label,
      fr.details.send,
      fr.details.missing.heapSize,
    ]) {
      expect(html).toContain(escaped(text))
    }
    const radios = html.match(/<input [^>]*type="radio"[^>]*>/g) ?? []
    expect(radios).toHaveLength(3 + 5)
    for (const radio of radios) expect(radio).not.toMatch(/\bchecked\b/)
    // Compteur « 0/280 » ; pas d'attribut maxlength (il compterait en UTF-16).
    expect(html).toContain('0/280')
    expect(html).not.toMatch(/maxlength/i)
    // « Envoyer » désactivé, relié à la raison affichée ; région annoncée.
    const button = html.match(/<button [^>]*>/g)?.find((tag) => tag.includes('aria-describedby')) ?? ''
    expect(button).toMatch(/\bdisabled\b/)
    const reasonId = button.match(/aria-describedby="([^"]+)"/)?.[1] ?? ''
    expect(html).toMatch(
      new RegExp(`<p id="${reasonId}"[^>]*>${escaped(fr.details.missing.heapSize)}</p>`),
    )
    expect(html).toMatch(/<p role="status"[^>]*>/)
    expect(html).toContain(escaped(fr.details.back))
  })

  it('écran 4 : remerciement, Numéro de suivi, Frise et bouton « Retour à l’accueil »', () => {
    const html = render(<ConfirmationPage />, { trackingNumber: 'TC-2026-000042', isDemo: false })
    expect(html).toContain(escaped(fr.confirmation.title))
    expect(html).toContain('TC-2026-000042')
    expect(html).toContain(escaped(fr.confirmation.home))
    expect(html).not.toContain(escaped(fr.confirmation.demo))
    expect(html).toContain('<ol')
  })

  it('écran 4 en Mode démonstration : étiquette « Données de démonstration »', () => {
    const html = render(<ConfirmationPage />, { trackingNumber: 'TC-2026-000042', isDemo: true })
    expect(html).toContain(escaped(fr.confirmation.demo))
  })

  it('écran 4 sans état de navigation (lien direct) : rien n’est affiché, retour à l’accueil', () => {
    expect(render(<ConfirmationPage />)).toBe('')
    expect(render(<ConfirmationPage />, { trackingNumber: 42 })).toBe('')
  })

  it('Frise de suivi : 4 étapes en liste ordonnée, « Signalé » courante et annoncée', () => {
    const html = render(<TrackingTimeline current="reported" />)
    const items = html.match(/<li[^>]*>.*?<\/li>/g) ?? []
    expect(items).toHaveLength(4)
    const labels = [
      fr.timeline.reported,
      fr.timeline.validated,
      fr.timeline.assigned,
      fr.timeline.collected,
    ]
    labels.forEach((label, index) => {
      expect(items[index]).toContain(escaped(label))
      // Pictogramme et libellé.
      expect(items[index]).toMatch(/<svg [^>]*aria-hidden="true"/)
    })
    const current = items.filter((item) => item.includes('aria-current="step"'))
    expect(current).toHaveLength(1)
    expect(current[0]).toContain(escaped(fr.timeline.reported))
    // Distinguée autrement que par la couleur : mention visible.
    expect(current[0]).toContain(escaped(fr.timeline.current))
    expect(html.match(new RegExp(escaped(fr.timeline.current), 'g'))).toHaveLength(1)
  })

  it('WasteTypePicker : 5 Types avec pictogramme et jeton de couleur, coche sur le Type choisi', () => {
    const none = render(<WasteTypePicker value={undefined} onChange={() => undefined} />)
    expect(none).not.toMatch(/\bchecked\b/)
    const chosen = render(<WasteTypePicker value="glass" onChange={() => undefined} />)
    const checked = chosen.match(/<input [^>]*checked[^>]*>/g) ?? []
    expect(checked).toHaveLength(1)
    expect(checked[0]).toContain('value="glass"')
    for (const { colorClass } of WASTE_TYPES) expect(chosen).toContain(colorClass)
    // Une coche de plus quand un Type est choisi (pictogrammes : un par Type).
    const svgs = (markup: string) => markup.match(/<svg /g)?.length ?? 0
    expect(svgs(chosen)).toBe(svgs(none) + 1)
  })

  it('WasteTypeBadge : pictogramme et libellé', () => {
    const html = render(<WasteTypeBadge type="organic" />)
    expect(html).toContain(escaped(fr.wasteType.organic))
    expect(html).toContain('text-waste-organic')
  })

  it('la page introuvable affiche son titre et un lien vers /', () => {
    const html = render(<NotFoundPage />)
    expect(html).toContain(escaped(fr.notFound.title))
    expect(html).toMatch(new RegExp(`<a [^>]*href="/"[^>]*>${escaped(fr.notFound.back)}</a>`))
  })
})
