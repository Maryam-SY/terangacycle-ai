// Pictogrammes SVG intégrés, dessinés pour TerangaCycle (aucune bibliothèque d'icônes).
// Toujours accompagnés d'un libellé visible : masqués aux lecteurs d'écran (aria-hidden).
// Couleur : currentColor, réglée par la classe text-* du parent ou une classe stroke-*.
import type { ReactNode } from 'react'

export interface IconProps {
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

/** Coche cerclée : option choisie, étape actuelle de la Frise de suivi. */
export function CheckIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <circle cx="12" cy="12" r="9" />
      <path d="M8 12.5l2.7 2.7L16 9.8" />
    </Icon>
  )
}

/** Avion en papier : envoi du Signalement. */
export function SendIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <path d="M21 3L3 10.5l7.5 3L13.5 21 21 3z" />
      <path d="M10.5 13.5L21 3" />
    </Icon>
  )
}

/** Petit tas : Taille de tas « petit ». */
export function HeapSmallIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <path d="M8 19a4 4 0 0 1 8 0" />
      <path d="M3 19h18" />
    </Icon>
  )
}

/** Tas moyen : Taille de tas « moyen ». */
export function HeapMediumIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <path d="M5 19a7 6 0 0 1 14 0" />
      <path d="M3 19h18" />
    </Icon>
  )
}

/** Grand tas : Taille de tas « grand ». */
export function HeapLargeIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <path d="M2.5 19C4 12 7.5 6 12 6s8 6 9.5 13" />
      <path d="M2 19h20" />
      <path d="M9 13h.01M14 11h.01M12 16h.01" />
    </Icon>
  )
}

/** Bouteille : plastique. */
export function BottleIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <path d="M10 2h4v3l2 3v12a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2V8l2-3V2z" />
      <path d="M8 12h8" />
    </Icon>
  )
}

/** Canette : métal. */
export function CanIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <path d="M7 5h10v14a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2V5z" />
      <path d="M8 2h8l1 3H7l1-3z" />
      <path d="M10 10v6" />
    </Icon>
  )
}

/** Bocal : verre. */
export function JarIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <path d="M8 3h8v3H8z" />
      <path d="M7 6h10a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2z" />
      <path d="M9 11v5" />
    </Icon>
  )
}

/** Feuille : organique. */
export function LeafIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <path d="M5 19C5 10 10 4 20 4c0 10-6 15-15 15z" />
      <path d="M5 19l8-8" />
    </Icon>
  )
}

/** Couches empilées : mixte. */
export function LayersIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <path d="M12 3l9 5-9 5-9-5 9-5z" />
      <path d="M3 12.5l9 5 9-5" />
      <path d="M3 16.5l9 5 9-5" />
    </Icon>
  )
}

/** Drapeau : étape « Signalé » de la Frise de suivi. */
export function FlagIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <path d="M5 21V4" />
      <path d="M5 4h11l-2 4 2 4H5" />
    </Icon>
  )
}

/** Bouclier coché : étape « Validé par la modération ». */
export function ShieldCheckIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <path d="M12 3l8 3v5c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-3z" />
      <path d="M9 12l2 2 4-4" />
    </Icon>
  )
}

/** Camion : étape « Assigné à un collecteur ». */
export function TruckIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <path d="M2 6h12v10H2z" />
      <path d="M14 9h4l3 3v4h-7" />
      <circle cx="6" cy="18" r="2" />
      <circle cx="17" cy="18" r="2" />
    </Icon>
  )
}

/** Photo cochée : étape « Collecté, preuve photo ». */
export function PhotoCheckIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <path d="M12 20H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v6" />
      <path d="M3 15l5-5 4 4" />
      <path d="M15 18l2 2 4-4" />
    </Icon>
  )
}
