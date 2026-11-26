import { useId, type ReactNode } from 'react'
import { useTranslation } from 'react-i18next'

import {
  BottleIcon,
  CanIcon,
  CheckIcon,
  JarIcon,
  LeafIcon,
  MixedIcon,
} from '../../ui/icons.tsx'
import { WASTE_TYPES, toggleWasteType, type WasteType } from './wasteTypes.ts'

// Composant unique des Types de déchet (story 1.13) : pictogramme, libellé et couleur de
// chaque type. L'état choisi est signalé par une coche et `aria-pressed`, jamais par la
// seule couleur ; chaque option mesure au moins 44 × 44 px.

const ICONS: Record<WasteType, (props: { className?: string }) => ReactNode> = {
  plastic: BottleIcon,
  metal: CanIcon,
  glass: JarIcon,
  organic: LeafIcon,
  mixed: MixedIcon,
}

/** Couleur du jeton de chaque type (classes Tailwind écrites en entier pour la génération). */
const COLOR: Record<WasteType, string> = {
  plastic: 'text-waste-plastic',
  metal: 'text-waste-metal',
  glass: 'text-waste-glass',
  organic: 'text-waste-organic',
  mixed: 'text-waste-mixed',
}

/** Pastille d'un Type de déchet : pictogramme coloré et libellé en Encre. */
export function WasteTypeBadge({ type }: { type: WasteType }) {
  const { t } = useTranslation()
  const TypeIcon = ICONS[type]
  return (
    <span className="inline-flex items-center gap-2 text-ink">
      <TypeIcon className={`size-6 shrink-0 ${COLOR[type]}`} />
      {t(`waste.${type}`)}
    </span>
  )
}

export function WasteTypePicker({
  value,
  onChange,
}: {
  value: WasteType | null
  onChange: (value: WasteType | null) => void
}) {
  const { t } = useTranslation()
  const labelId = useId()
  return (
    <fieldset className="flex flex-col gap-2" aria-labelledby={labelId}>
      <legend id={labelId} className="text-lg font-semibold text-brand-900">
        {t('details.wasteType.label')}{' '}
        <span className="text-base font-normal text-muted">{t('details.optional')}</span>
      </legend>
      <div className="grid grid-cols-2 gap-2">
        {WASTE_TYPES.map((type) => {
          const selected = value === type
          return (
            <button
              key={type}
              type="button"
              aria-pressed={selected}
              onClick={() => onChange(toggleWasteType(value, type))}
              className={`flex min-h-12 items-center justify-between gap-2 rounded-xl border-2 px-3 text-left focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-900 ${
                selected ? 'border-brand-600 bg-mint' : 'border-line bg-surface'
              }`}
            >
              <WasteTypeBadge type={type} />
              {selected && <CheckIcon className="size-6 shrink-0 text-brand-600" />}
            </button>
          )
        })}
      </div>
    </fieldset>
  )
}
