// Budget de poids de l'accueil (NFR-5) : au plus 500 Ko pour le HTML, le JS, le CSS et les
// polices précachés, hors images et Modèle. Lancer après `npm run build`.
//
// Fichiers mesurés : la liste de précache de dist/sw.js (ce que l'appareil télécharge pour
// ouvrir l'accueil, hors ligne compris), plus sw.js et le runtime Workbox qu'il charge ;
// images et manifeste exclus.
// Poids mesuré : celui du transfert. HTML, JS et CSS sont compressés par Caddy
// (`encode zstd gzip`), donc comptés en gzip niveau 5 (niveau par défaut de Caddy, moins
// serré que zstd) ; les polices woff2, déjà compressées, comptent pour leur taille brute.
import { existsSync, readFileSync } from 'node:fs'
import { gzipSync } from 'node:zlib'

const BUDGET = 500_000
const DIST = new URL('../dist/', import.meta.url)
const COMPRESSED = /\.(html|js|mjs|css)$/
const FONT = /\.woff2$/

function fail(message) {
  console.error(`Budget de poids : ${message}`)
  process.exit(1)
}

const swFile = new URL('sw.js', DIST)
if (!existsSync(swFile)) fail('dist/sw.js absent : lancer npm run build avant npm run size.')

const sw = readFileSync(swFile, 'utf8')
// Chemins relatifs à dist/ (un éventuel `/` initial est retiré).
const precached = [...sw.matchAll(/\burl:\s*"([^"]+)"/g)].map((match) =>
  match[1].replace(/^\/+/, ''),
)
if (precached.length === 0) fail('aucune entrée de précache trouvée dans dist/sw.js.')

// Runtime Workbox chargé par sw.js (`define(['./workbox-…'], …)`), hors liste de précache.
const swImports = [...sw.matchAll(/["']\.\/(workbox-[\w-]+?)(?:\.js)?["']/g)].map(
  (match) => `${match[1]}.js`,
)

const files = [...new Set(['sw.js', ...swImports, ...precached])].filter(
  (path) => COMPRESSED.test(path) || FONT.test(path),
)
if (!files.some((path) => path.endsWith('.html'))) fail('index.html absent du précache.')

const missing = files.filter((path) => !existsSync(new URL(path, DIST)))
if (missing.length > 0) fail(`fichier(s) du précache absent(s) de dist/ : ${missing.join(', ')}.`)

const rows = files.map((path) => {
  const bytes = readFileSync(new URL(path, DIST))
  const weight = FONT.test(path) ? bytes.length : gzipSync(bytes, { level: 5 }).length
  return { path, raw: bytes.length, weight }
})

const total = rows.reduce((sum, row) => sum + row.weight, 0)
const kb = (bytes) => `${(bytes / 1000).toFixed(1)} Ko`
for (const row of rows) {
  console.log(`${kb(row.weight).padStart(10)}  (brut ${kb(row.raw).padStart(9)})  ${row.path}`)
}
console.log(`${kb(total).padStart(10)}  total transféré, budget ${kb(BUDGET)}`)

if (total > BUDGET) fail(`${kb(total)} dépasse ${kb(BUDGET)}.`)
