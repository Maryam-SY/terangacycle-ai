// Réglages PWA partagés par vite.config.ts et les tests (src/pwa.test.ts).

// Le manifeste ne peut pas lire les variables CSS : ces valeurs doivent rester égales à
// --color-brand-900 et --color-surface de src/theme/theme.css (vérifié par un test).
export const THEME_COLOR = '#0B3D2E'
export const BACKGROUND_COLOR = '#F6FAF7'

// L'API et les sondes ne sont jamais servies par index.html hors ligne.
export const NAVIGATE_FALLBACK_DENYLIST: RegExp[] = [/^\/v1\//, /^\/healthz/, /^\/readyz/]

// Précache : la coquille, et seulement les sous-ensembles latin et latin-ext d'Inter
// (français, wolof) ; les autres restent chargés à la demande. Le manifeste et ses icônes
// PNG sont ajoutés par vite-plugin-pwa lui-même : les reprendre ici les dupliquerait.
export const PRECACHE_GLOB_PATTERNS = [
  '**/*.{js,css,html}',
  'assets/inter-latin-wght-normal-*.woff2',
  'assets/inter-latin-ext-wght-normal-*.woff2',
]
