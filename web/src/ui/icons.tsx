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

/** Micro : enregistrer une description à voix haute. */
export function MicIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <rect x="9" y="3" width="6" height="11" rx="3" />
      <path d="M5 11a7 7 0 0 0 14 0M12 18v3" />
    </Icon>
  )
}

/** Carré : arrêter l'enregistrement. */
export function StopIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <rect x="6" y="6" width="12" height="12" rx="2" />
    </Icon>
  )
}

/** Corbeille : effacer la note vocale. */
export function TrashIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3" />
    </Icon>
  )
}

/** Coche : option choisie (jamais signalée par la seule couleur). */
export function CheckIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <path d="M5 12l5 5 9-10" />
    </Icon>
  )
}

/** Avion en papier : envoyer. */
export function SendIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <path d="M21 3L10 14M21 3l-7 18-4-7-7-4 18-7z" />
    </Icon>
  )
}

/** Bouteille : plastique. */
export function BottleIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <path d="M10 2h4v3l2 3v12a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2V8l2-3V2zM8 12h8" />
    </Icon>
  )
}

/** Canette : métal. */
export function CanIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <ellipse cx="12" cy="5" rx="5" ry="2" />
      <path d="M7 5v14c0 1.1 2.2 2 5 2s5-.9 5-2V5" />
    </Icon>
  )
}

/** Bocal : verre. */
export function JarIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <path d="M8 3h8v3H8zM7 6h10l1 3v10a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V9l1-3z" />
    </Icon>
  )
}

/** Feuille : organique. */
export function LeafIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <path d="M5 19c0-9 6-14 15-15-1 9-6 15-15 15zM5 19l7-7" />
    </Icon>
  )
}

/** Cartons empilés : mixte. */
export function MixedIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <rect x="3" y="12" width="8" height="8" />
      <rect x="13" y="12" width="8" height="8" />
      <rect x="8" y="4" width="8" height="8" />
    </Icon>
  )
}

/** Tas : petit, moyen ou grand selon le nombre de cercles. */
export function PileIcon({ className, level }: IconProps & { level: 1 | 2 | 3 }) {
  return (
    <Icon className={className}>
      <path d="M3 20h18" />
      <circle cx="12" cy="17" r="2.5" />
      {level >= 2 && <circle cx="7.5" cy="17" r="2.5" />}
      {level >= 2 && <circle cx="16.5" cy="17" r="2.5" />}
      {level >= 3 && <circle cx="9.5" cy="12.5" r="2.5" />}
      {level >= 3 && <circle cx="14.5" cy="12.5" r="2.5" />}
      {level >= 3 && <circle cx="12" cy="8" r="2.5" />}
    </Icon>
  )
}

/** Drapeau : étape « Signalé ». */
export function FlagIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <path d="M5 21V4M5 4h12l-2 4 2 4H5" />
    </Icon>
  )
}

/** Bouclier coché : étape « Validé par la modération ». */
export function ShieldCheckIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3z" />
      <path d="M8.5 12l2.5 2.5 4.5-5" />
    </Icon>
  )
}

/** Camion : étape « Assigné à un collecteur ». */
export function TruckIcon({ className }: IconProps) {
  return (
    <Icon className={className}>
      <path d="M2 6h12v10H2zM14 10h4l3 3v3h-7" />
      <circle cx="6" cy="18" r="2" />
      <circle cx="17" cy="18" r="2" />
    </Icon>
  )
}
