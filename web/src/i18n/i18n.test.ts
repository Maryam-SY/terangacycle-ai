// Garde-fous de la coquille (story 1.3) : traductions alignées et thème unique.
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs'
import { join, relative } from 'node:path'
import { fileURLToPath } from 'node:url'

import { describe, expect, it } from 'vitest'

const WEB = fileURLToPath(new URL('../..', import.meta.url))
const SRC = join(WEB, 'src')
const THEME = join(SRC, 'theme', 'theme.css')
// Ancien vert de la maquette, interdit (écrit en deux morceaux pour ne pas se trouver lui-même).
const FORBIDDEN_GREEN = '#1F8A' + '5B'
const SKIPPED_DIRS = new Set(['node_modules', 'dist', 'dev-dist', '.git'])

function walk(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    if (SKIPPED_DIRS.has(name)) return []
    const path = join(dir, name)
    return statSync(path).isDirectory() ? walk(path) : [path]
  })
}

function flatKeys(value: unknown, prefix = ''): string[] {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) return [prefix]
  return Object.entries(value).flatMap(([key, child]) =>
    flatKeys(child, prefix ? `${prefix}.${key}` : key),
  )
}

function readJson(name: string): unknown {
  return JSON.parse(readFileSync(join(SRC, 'i18n', name), 'utf8'))
}

describe('traductions', () => {
  it('fr.json et wo.json ont exactement les mêmes clés', () => {
    const fr = flatKeys(readJson('fr.json')).sort()
    const wo = flatKeys(readJson('wo.json')).sort()
    expect(fr.length).toBeGreaterThan(0)
    expect(wo).toEqual(fr)
  })

  it('aucune valeur vide', () => {
    for (const name of ['fr.json', 'wo.json']) {
      const values = JSON.stringify(readJson(name))
      expect(values, name).not.toContain('""')
    }
  })
})

describe('thème', () => {
  it(`aucun fichier de src/ ne contient ${FORBIDDEN_GREEN}`, () => {
    const offenders = walk(SRC).filter((file) =>
      readFileSync(file, 'utf8').toUpperCase().includes(FORBIDDEN_GREEN),
    )
    expect(offenders.map((file) => relative(WEB, file))).toEqual([])
  })

  it('theme.css contient un seul bloc @theme', () => {
    const css = readFileSync(THEME, 'utf8')
    expect(css.match(/@theme\b/g) ?? []).toHaveLength(1)
  })

  it('aucune couleur écrite hors de theme.css', () => {
    const hex = /#[0-9a-f]{3,8}\b/i
    const offenders = walk(SRC)
      .filter((file) => /\.(css|tsx?)$/.test(file) && file !== THEME && !file.endsWith('.test.ts'))
      .filter((file) => hex.test(readFileSync(file, 'utf8')))
    expect(offenders.map((file) => relative(WEB, file))).toEqual([])
  })

  it('ni tailwind.config.* ni @config', () => {
    const files = walk(WEB)
    expect(files.filter((file) => /^tailwind\.config\./.test(file.split(/[\\/]/).pop() ?? ''))).toEqual([])
    const withConfig = files
      .filter((file) => file.endsWith('.css'))
      .filter((file) => /@config\b/.test(readFileSync(file, 'utf8')))
    expect(withConfig.map((file) => relative(WEB, file))).toEqual([])
    expect(existsSync(THEME)).toBe(true)
  })
})
