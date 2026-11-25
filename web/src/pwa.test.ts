// Réglages du service worker et du manifeste (pwa.config.ts).
import { existsSync, readFileSync } from 'node:fs'

import { describe, expect, it } from 'vitest'

import {
  BACKGROUND_COLOR,
  MANIFEST,
  NAVIGATE_FALLBACK_DENYLIST,
  THEME_COLOR,
} from '../pwa.config.ts'

const THEME_CSS = readFileSync(new URL('./theme/theme.css', import.meta.url), 'utf8')

function themeColor(name: string): string {
  const match = THEME_CSS.match(new RegExp(`--color-${name}:\\s*(#[0-9a-fA-F]{3,8})\\s*;`))
  if (!match) throw new Error(`--color-${name} absent de theme.css`)
  return match[1].toUpperCase()
}

const PUBLIC = new URL('../public/', import.meta.url)
const PNG_SIGNATURE = '89504e470d0a1a0a'

/** Largeur et hauteur d'un PNG, lues dans son en-tête IHDR. */
function pngSize(file: URL): string {
  const bytes = readFileSync(file)
  expect(bytes.subarray(0, 8).toString('hex'), file.pathname).toBe(PNG_SIGNATURE)
  return `${bytes.readUInt32BE(16)}x${bytes.readUInt32BE(20)}`
}

function denied(path: string): boolean {
  return NAVIGATE_FALLBACK_DENYLIST.some((pattern) => pattern.test(path))
}

describe('service worker', () => {
  it.each(['/v1/config', '/healthz', '/readyz'])('%s ne reçoit jamais index.html', (path) => {
    expect(denied(path)).toBe(true)
  })

  it.each(['/', '/n-importe-quoi'])('%s reçoit index.html hors ligne', (path) => {
    expect(denied(path)).toBe(false)
  })
})

describe('manifeste', () => {
  it('theme_color = --color-brand-900', () => {
    expect(THEME_COLOR.toUpperCase()).toBe(themeColor('brand-900'))
  })

  it('background_color = --color-surface', () => {
    expect(BACKGROUND_COLOR.toUpperCase()).toBe(themeColor('surface'))
  })

  it('nom « TerangaCycle AI », affichage autonome', () => {
    expect(MANIFEST.name).toBe('TerangaCycle AI')
    expect(MANIFEST.display).toBe('standalone')
    expect(MANIFEST.theme_color).toBe(THEME_COLOR)
    expect(MANIFEST.background_color).toBe(BACKGROUND_COLOR)
  })

  it('icônes 192 et 512, dont une maskable de 512', () => {
    const icons = MANIFEST.icons.map((icon) => ({
      sizes: icon.sizes,
      purpose: 'purpose' in icon ? icon.purpose : 'any',
    }))
    expect(icons).toEqual([
      { sizes: '192x192', purpose: 'any' },
      { sizes: '512x512', purpose: 'any' },
      { sizes: '512x512', purpose: 'maskable' },
    ])
  })

  it.each(MANIFEST.icons.map((icon) => [icon.src, icon.sizes]))(
    '%s existe dans public/ et mesure %s',
    (src, sizes) => {
      const file = new URL(src.replace(/^\//, ''), PUBLIC)
      expect(existsSync(file), src).toBe(true)
      expect(pngSize(file)).toBe(sizes)
    },
  )
})
