// Chemins de la PWA, partagés par la table des routes et les liens.
export const PATHS = {
  home: '/',
  /** Entrée du signalement : redirige vers le consentement ou vers la capture. */
  report: '/signaler',
  consent: '/signaler/consentement',
  capture: '/signaler/capture',
  /** Écran 3 : détails (taille du tas, type, commentaire) et envoi. */
  details: '/signaler/details',
} as const
