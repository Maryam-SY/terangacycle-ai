// Pictogrammes SVG intégrés, dessinés pour TerangaCycle (aucune bibliothèque d'icônes).
// Toujours accompagnés d'un libellé visible : masqués aux lecteurs d'écran (aria-hidden).
// Couleur : currentColor, réglée par la classe text-* du parent ou une classe stroke-*.
import type { ReactNode } from 'react'

interface IconProps {
  className?: string
}

function Icon({ className, children }: IconProps & { children: ReactNode }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      className={className ?? 'size-6'}
    >
      {children}
    </svg>
  )
}

/** Appareil photo : action « Signaler un dépôt ». */
export function CameraIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <path d="M4 8h3l2-3h6l2 3h3a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z" />
      <circle cx="12" cy="13.5" r="3.5" />
    </Icon>
  )
}

/** Repère de position : géolocalisation. */
export function LocationIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z" />
      <circle cx="12" cy="9.5" r="2.5" />
    </Icon>
  )
}

/** Photo et flèche montante : envoi de la photo. */
export function PhotoSendIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <path d="M13 4H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-6" />
      <path d="M3 16l5-5 4 4 2-2 5 5" />
      <path d="M19 9V3M16 6l3-3 3 3" />
    </Icon>
  )
}

/** Personne barrée : consigne « ni personne ni plaque ». */
export function NoPersonIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <circle cx="12" cy="8" r="3" />
      <path d="M6 20v-1a6 6 0 0 1 12 0v1" />
      <path d="M4 4l16 16" />
    </Icon>
  )
}

/** Téléphone : Identifiant d'appareil anonyme. */
export function PhoneIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <rect x="6" y="2.5" width="12" height="19" rx="2" />
      <path d="M11 18h2" />
    </Icon>
  )
}

/** Cœur : contribution à l'amélioration du Modèle. */
export function HeartIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <path d="M12 20s-7.5-4.6-7.5-10.2A4.3 4.3 0 0 1 12 7.2a4.3 4.3 0 0 1 7.5 2.6C19.5 15.4 12 20 12 20z" />
    </Icon>
  )
}

/** Information : avertissement non bloquant. */
export function InfoIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v5M12 8h.01" />
    </Icon>
  )
}

/** Alerte : message d'erreur (icône rouge, texte en Encre). */
export function AlertIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <path d="M12 3l9.5 17h-19L12 3z" />
      <path d="M12 10v4M12 17h.01" />
    </Icon>
  )
}
