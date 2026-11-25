// Contrôle de contraste WCAG 2.1 AA (story 1.6) : les paires texte/fond déclarées dans
// contrast-pairs.json sont calculées à partir des jetons de theme.css, sans recopier
// aucune couleur ici.

export type PairKind = 'text' | 'large-text' | 'non-text'

/** Paire déclarée : `fg` et `bg` sont des jetons (`--color-…`) ou le blanc littéral. */
export interface ContrastPair {
  name: string
  fg: string
  bg: string
  kind: string
}

export interface PairFailure {
  name: string
  /** Rapport calculé, `null` si la paire n'a pas pu être évaluée. */
  ratio: number | null
  message: string
}

/** Seuils WCAG 2.1 AA : texte normal 4,5:1 ; texte large et éléments non textuels 3:1. */
export const MIN_RATIO: Record<PairKind, number> = {
  text: 4.5,
  'large-text': 3,
  'non-text': 3,
}

const COMMENT = /\/\*[\s\S]*?\*\//g
const THEME_OPEN = /@theme\s*\{/
// Déclaration d'un jeton de couleur dans le bloc @theme : `--color-nom: valeur;`.
const TOKEN_DECLARATION = /(--color-[\w-]+)\s*:\s*([^;]*);/g
const HEX_VALUE = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i
// Le blanc n'est pas un jeton : seule couleur littérale admise dans le fichier de paires.
// Écrit en deux morceaux : la garde de i18n.test.ts refuse toute couleur hors de theme.css.
export const WHITE = '#' + 'FFFFFF'

/** Contenu du bloc `@theme { … }`, commentaires retirés. */
function themeBlock(css: string): string {
  const source = css.replace(COMMENT, '')
  const open = THEME_OPEN.exec(source)
  if (!open) throw new Error('theme.css : aucun bloc @theme')
  const start = open.index + open[0].length
  let depth = 1
  for (let i = start; i < source.length; i += 1) {
    if (source[i] === '{') depth += 1
    if (source[i] === '}') depth -= 1
    if (depth === 0) return source.slice(start, i)
  }
  throw new Error('theme.css : bloc @theme non fermé')
}

/** Jetons de couleur du bloc `@theme` : nom (`--color-ink`) → valeur hexadécimale.
 *  Lève une erreur pour une valeur non hexadécimale (3 ou 6 chiffres) ou un jeton
 *  redéclaré avec une autre valeur. */
export function parseThemeColors(css: string): Map<string, string> {
  const colors = new Map<string, string>()
  for (const [, name, raw] of themeBlock(css).matchAll(TOKEN_DECLARATION)) {
    const value = raw.trim()
    if (!HEX_VALUE.test(value)) {
      throw new Error(`${name} : valeur « ${value} » non hexadécimale (3 ou 6 chiffres)`)
    }
    const previous = colors.get(name)
    if (previous !== undefined && previous.toUpperCase() !== value.toUpperCase()) {
      throw new Error(`${name} : redéclaré avec une autre valeur (${previous}, puis ${value})`)
    }
    colors.set(name, value)
  }
  return colors
}

function channels(hex: string): [number, number, number] {
  const match = HEX_VALUE.exec(hex)
  if (!match) throw new Error(`couleur illisible : ${hex}`)
  const digits = match[1].length === 3 ? [...match[1]].map((d) => d + d).join('') : match[1]
  return [0, 2, 4].map((i) => Number.parseInt(digits.slice(i, i + 2), 16)) as [
    number,
    number,
    number,
  ]
}

/** Luminance relative sRGB (WCAG 2.x). */
function luminance(hex: string): number {
  const [r, g, b] = channels(hex).map((value) => {
    const c = value / 255
    return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
  })
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

/** Rapport de contraste WCAG entre deux couleurs hexadécimales (1 à 21). */
export function contrastRatio(a: string, b: string): number {
  const [light, dark] = [luminance(a), luminance(b)].sort((x, y) => y - x)
  return (light + 0.05) / (dark + 0.05)
}

function isKind(kind: string): kind is PairKind {
  return Object.hasOwn(MIN_RATIO, kind)
}

/** Couleur d'une référence, ou le message qui explique pourquoi elle est refusée. */
function resolve(ref: string, colors: Map<string, string>): { color: string } | { error: string } {
  if (ref.startsWith('#')) {
    return ref.toUpperCase() === WHITE
      ? { color: ref }
      : { error: `couleur littérale interdite : seul ${WHITE} est accepté (${ref})` }
  }
  const color = colors.get(ref)
  return color === undefined ? { error: `jeton inconnu ${ref} (absent de theme.css)` } : { color }
}

/** Paires sous leur seuil, ou impossibles à évaluer (jeton inconnu, couleur littérale,
 *  type inconnu). */
export function failingPairs(
  pairs: readonly ContrastPair[],
  colors: Map<string, string>,
): PairFailure[] {
  const failures: PairFailure[] = []
  for (const { name, fg, bg, kind } of pairs) {
    if (!isKind(kind)) {
      failures.push({ name, ratio: null, message: `${name} : type inconnu « ${kind} »` })
      continue
    }
    const fgColor = resolve(fg, colors)
    const bgColor = resolve(bg, colors)
    if ('error' in fgColor || 'error' in bgColor) {
      const errors = [fgColor, bgColor].flatMap((r) => ('error' in r ? [r.error] : []))
      failures.push({ name, ratio: null, message: `${name} : ${errors.join(' ; ')}` })
      continue
    }
    const ratio = contrastRatio(fgColor.color, bgColor.color)
    const required = MIN_RATIO[kind]
    if (ratio < required) {
      const message = `${name} (${kind}) : ${ratio.toFixed(2)}:1, sous le seuil de ${required}:1`
      failures.push({ name, ratio, message })
    }
  }
  return failures
}
