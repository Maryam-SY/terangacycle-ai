// Les 5 Types de déchet (story 1.13), dans l'ordre des classes du Modèle (AD-7) : code de
// l'API, pictogramme, jeton de couleur provisoire (`--color-waste-*` de theme.css) et clé
// du libellé (`wasteType.*`). Source unique de WasteTypeBadge et WasteTypePicker.
import type { ComponentType } from 'react'

import type { WasteType } from '../../api/reports.ts'
import {
  BottleIcon,
  CanIcon,
  JarIcon,
  LayersIcon,
  LeafIcon,
  type IconProps,
} from '../../ui/icons.tsx'

export interface WasteTypeInfo {
  value: WasteType
  icon: ComponentType<IconProps>
  /** Classe Tailwind tirée du jeton `--color-waste-<type>` : couleur du pictogramme. */
  colorClass: string
  labelKey: `wasteType.${WasteType}`
}

export const WASTE_TYPES: readonly WasteTypeInfo[] = [
  { value: 'plastic', icon: BottleIcon, colorClass: 'text-waste-plastic', labelKey: 'wasteType.plastic' },
  { value: 'metal', icon: CanIcon, colorClass: 'text-waste-metal', labelKey: 'wasteType.metal' },
  { value: 'glass', icon: JarIcon, colorClass: 'text-waste-glass', labelKey: 'wasteType.glass' },
  { value: 'organic', icon: LeafIcon, colorClass: 'text-waste-organic', labelKey: 'wasteType.organic' },
  { value: 'mixed', icon: LayersIcon, colorClass: 'text-waste-mixed', labelKey: 'wasteType.mixed' },
]

export function wasteTypeInfo(value: WasteType): WasteTypeInfo {
  const info = WASTE_TYPES.find((type) => type.value === value)
  if (!info) throw new RangeError(`Type de déchet inconnu : ${value}`)
  return info
}

/** Nouveau choix après un toucher : toucher le Type déjà choisi le retire. */
export function toggleWasteType(current: WasteType | undefined, touched: WasteType): WasteType | undefined {
  return current === touched ? undefined : touched
}
