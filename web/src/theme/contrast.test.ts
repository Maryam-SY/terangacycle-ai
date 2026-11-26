// Contraste WCAG 2.1 AA des paires déclarées (story 1.6), calculé depuis theme.css.
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join, relative } from 'node:path'
import { fileURLToPath } from 'node:url'

import { describe, expect, it } from 'vitest'

import { contrastRatio, failingPairs, parseThemeColors, type ContrastPair } from './contrast'
import pairs from './contrast-pairs.json'

const SRC = fileURLToPath(new URL('..', import.meta.url))
const css = readFileSync(fileURLToPath(new URL('./theme.css', import.meta.url)), 'utf8')
const colors = parseThemeColors(css)
const WHITE = '#FFFFFF'

function walk(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name)
    return statSync(path).isDirectory() ? walk(path) : [path]
  })
}

describe('contraste des jetons', () => {
  it('lit les jetons de couleur de theme.css', () => {
    expect(colors.get('--color-brand-600')).toBe('#187A50')
    expect(colors.size).toBeGreaterThanOrEqual(11)
  })

  it('toutes les paires réelles atteignent leur seuil', () => {
    expect(pairs.length).toBeGreaterThan(0)
    expect(failingPairs(pairs, colors).map((failure) => failure.message)).toEqual([])
  })

  it('chaque couleur de Type de déchet est déclarée face à surface et au blanc (non textuel)', () => {
    const tokens = [...colors.keys()].filter((name) => name.startsWith('--color-waste-'))
    expect(tokens.map((name) => name.replace('--color-waste-', '')).sort()).toEqual(
      ['glass', 'metal', 'mixed', 'organic', 'plastic'],
    )
    for (const token of tokens) {
      for (const bg of ['--color-surface', WHITE]) {
        const declared = pairs.some(
          (pair) =>
            pair.fg === token && pair.bg.toUpperCase() === bg.toUpperCase() && pair.kind === 'non-text',
        )
        expect(declared, `${token} sur ${bg}`).toBe(true)
      }
    }
  })

  it('chaque paire a un nom unique', () => {
    const names = pairs.map((pair) => pair.name)
    expect(new Set(names).size).toBe(names.length)
  })

  it('témoin : le rouge en texte normal sur blanc échoue en nommant la paire', () => {
    const witness: ContrastPair[] = [
      { name: 'témoin danger/white', fg: '--color-danger', bg: WHITE, kind: 'text' },
    ]
    const failures = failingPairs(witness, colors)
    expect(failures).toHaveLength(1)
    const [failure] = failures
    expect(failure.name).toBe('témoin danger/white')
    expect(failure.ratio).toBeGreaterThanOrEqual(4.27)
    expect(failure.ratio).toBeLessThanOrEqual(4.29)
    expect(failure.message).toContain('témoin danger/white')
    expect(failure.message).toMatch(/4\.2[789]:1/)
  })

  it('le même rouge en élément non textuel passe (≥ 3:1)', () => {
    const witness: ContrastPair[] = [
      { name: 'témoin danger/white', fg: '--color-danger', bg: WHITE, kind: 'non-text' },
    ]
    expect(failingPairs(witness, colors)).toEqual([])
  })

  it('un jeton inconnu échoue explicitement', () => {
    const witness: ContrastPair[] = [
      { name: 'témoin inconnu', fg: '--color-inexistant', bg: WHITE, kind: 'text' },
    ]
    const failures = failingPairs(witness, colors)
    expect(failures).toHaveLength(1)
    expect(failures[0].ratio).toBeNull()
    expect(failures[0].message).toBe(
      'témoin inconnu : jeton inconnu --color-inexistant (absent de theme.css)',
    )
  })

  it('une couleur littérale autre que le blanc est refusée', () => {
    const witness: ContrastPair[] = [
      { name: 'témoin littéral', fg: '#000000', bg: WHITE, kind: 'text' },
    ]
    expect(failingPairs(witness, colors).map((failure) => failure.message)).toEqual([
      'témoin littéral : couleur littérale interdite : seul #FFFFFF est accepté (#000000)',
    ])
  })

  it('le blanc littéral est accepté quelle que soit la casse', () => {
    const witness: ContrastPair[] = [
      { name: 'témoin blanc', fg: '--color-ink', bg: '#ffffff', kind: 'text' },
    ]
    expect(failingPairs(witness, colors)).toEqual([])
  })

  it('un type de paire inconnu échoue', () => {
    const witness: ContrastPair[] = [
      { name: 'témoin type', fg: '--color-ink', bg: WHITE, kind: 'huge-text' },
    ]
    expect(failingPairs(witness, colors)[0].message).toBe('témoin type : type inconnu « huge-text »')
  })

  it('#187A50 sur blanc vaut 5,33:1 (formule WCAG)', () => {
    expect(Math.abs(contrastRatio('#187A50', WHITE) - 5.33)).toBeLessThanOrEqual(0.01)
    expect(contrastRatio(WHITE, '#187A50')).toBe(contrastRatio('#187A50', WHITE))
    expect(contrastRatio('#000', '#fff')).toBeCloseTo(21, 5)
  })
})

describe('lecture de theme.css', () => {
  it('ne lit que le bloc @theme, commentaires retirés', () => {
    const source = `
      :root { --color-dehors: #000000; }
      @theme {
        /* --color-commente: #111111; */
        --color-a: #FFFFFF;
        --color-b: #abc;
      }
      .x { --color-apres: #222222; }`
    expect([...parseThemeColors(source)]).toEqual([
      ['--color-a', '#FFFFFF'],
      ['--color-b', '#abc'],
    ])
  })

  it('refuse un jeton de couleur non hexadécimal', () => {
    expect(() => parseThemeColors('@theme { --color-a: oklch(0.5 0.1 120); }')).toThrow(
      '--color-a : valeur « oklch(0.5 0.1 120) » non hexadécimale (3 ou 6 chiffres)',
    )
    expect(() => parseThemeColors('@theme { --color-a: #12345678; }')).toThrow('non hexadécimale')
  })

  it('refuse un jeton redéclaré avec une autre valeur', () => {
    expect(() =>
      parseThemeColors('@theme { --color-a: #FFFFFF; --color-a: #000000; }'),
    ).toThrow('--color-a : redéclaré avec une autre valeur (#FFFFFF, puis #000000)')
    expect(parseThemeColors('@theme { --color-a: #FFFFFF; --color-a: #ffffff; }').size).toBe(1)
  })

  it('refuse un fichier sans bloc @theme', () => {
    expect(() => parseThemeColors(':root { --color-a: #FFFFFF; }')).toThrow('aucun bloc @theme')
  })
})

describe('rouge en texte', () => {
  // Le rouge (danger) fait 4,28:1 sur blanc : jamais en texte normal (aplat, icône, bordure).
  it('aucun fichier de src/ n’utilise la classe text-danger', () => {
    const offenders = walk(SRC)
      .filter((file) => /\.(css|tsx?)$/.test(file) && !/\.test\.tsx?$/.test(file))
      .filter((file) => /\btext-danger\b/.test(readFileSync(file, 'utf8')))
    expect(offenders.map((file) => relative(SRC, file))).toEqual([])
  })
})
