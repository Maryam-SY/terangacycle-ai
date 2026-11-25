// Chemins de la PWA, partagés par la table des routes et les liens.
export const PATHS = {
  home: '/',
  /** Entrée du signalement : redirige vers le consentement ou vers la capture. */
  report: '/signaler',
  consent: '/signaler/consentement',
  capture: '/signaler/capture',
  /** Écran 3 · Détails : provisoire, lit le brouillon (story 1.13 pour la suite). */
  details: '/signaler/details',
} as const
