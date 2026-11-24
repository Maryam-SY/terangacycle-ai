// Réglages du service worker et du manifeste (pwa.config.ts).
import { readFileSync } from 'node:fs'

import { describe, expect, it } from 'vitest'

import { BACKGROUND_COLOR, NAVIGATE_FALLBACK_DENYLIST, THEME_COLOR } from '../pwa.config.ts'

const THEME_CSS = readFileSync(new URL('./theme/theme.css', import.meta.url), 'utf8')

function themeColor(name: string): string {
  const match = THEME_CSS.match(new RegExp(`--color-${name}:\\s*(#[0-9a-fA-F]{3,8})\\s*;`))
  if (!match) throw new Error(`--color-${name} absent de theme.css`)
  return match[1].toUpperCase()
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
})
