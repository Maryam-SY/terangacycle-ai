// Chemins de la PWA, partagés par la table des routes et les liens.
export const PATHS = {
  home: '/',
  /** Entrée du signalement : redirige vers le consentement ou vers la capture. */
  report: '/signaler',
  consent: '/signaler/consentement',
  capture: '/signaler/capture',
  /** Écran 3 · Détails : Taille de tas, Type de déchet, commentaire et envoi (story 1.13). */
  details: '/signaler/details',
  /** Écran 4 · Confirmation : Numéro de suivi et Frise de suivi, après l'envoi. */
  confirmation: '/signaler/confirmation',
} as const
