// Règle de lint d'AD-11 : `fetch` interdit hors de src/api/ et src/offline/, y compris
// par `window.fetch`, `globalThis.fetch` et `self.fetch`.
// oxlint tourne avec la vraie configuration (.oxlintrc.json) sur des fichiers témoins
// écrits dans un dossier temporaire qui reproduit l'arborescence de src/.
import { spawnSync } from 'node:child_process'
import { copyFileSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

import { afterAll, beforeAll, describe, expect, it } from 'vitest'

const WEB = fileURLToPath(new URL('..', import.meta.url))
const OXLINT = join(WEB, 'node_modules', 'oxlint', 'bin', 'oxlint')
// Forme d'appel -> règle oxlint qui doit la refuser hors de src/api/ et src/offline/.
const FORMS: Record<string, string> = {
  fetch: 'no-restricted-globals',
  'window.fetch': 'no-restricted-properties',
  'globalThis.fetch': 'no-restricted-properties',
  'self.fetch': 'no-restricted-properties',
}
const DIRS = ['src/features', 'src/api', 'src/offline']

let root = ''

function witness(dir: string, form: string): string {
  return `${dir}/${form.replace('.', '-')}.ts`
}

function lint(file: string): { status: number | null; output: string } {
  const result = spawnSync(process.execPath, [OXLINT, '-c', '.oxlintrc.json', file], {
    cwd: root,
    encoding: 'utf8',
  })
  return { status: result.status, output: `${result.stdout}${result.stderr}` }
}

beforeAll(() => {
  root = mkdtempSync(join(tmpdir(), 'oxlint-fetch-'))
  copyFileSync(join(WEB, '.oxlintrc.json'), join(root, '.oxlintrc.json'))
  for (const dir of DIRS) {
    mkdirSync(join(root, dir), { recursive: true })
    for (const form of Object.keys(FORMS)) {
      writeFileSync(
        join(root, witness(dir, form)),
        `export const load = (): Promise<Response> => ${form}('/v1/config')\n`,
      )
    }
  }
})

afterAll(() => {
  if (root) rmSync(root, { recursive: true, force: true })
})

describe('fetch hors de src/api/ et src/offline/', () => {
  it.each(Object.entries(FORMS))('%s est une erreur de lint dans src/features/', (form, rule) => {
    const { status, output } = lint(witness('src/features', form))
    expect(status).not.toBe(0)
    expect(output).toContain(rule)
  })

  it.each(
    ['src/api', 'src/offline'].flatMap((dir) => Object.keys(FORMS).map((form) => [dir, form])),
  )('est autorisé dans %s (%s)', (dir, form) => {
    const { status, output } = lint(witness(dir, form))
    expect(output).not.toContain('no-restricted-')
    expect(status).toBe(0)
  })
})
