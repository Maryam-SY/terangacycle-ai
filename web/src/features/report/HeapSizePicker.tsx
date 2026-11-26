import { useId, type ComponentType } from 'react'
import { useTranslation } from 'react-i18next'

import type { HeapSize } from '../../api/reports.ts'
import {
  CheckIcon,
  HeapLargeIcon,
  HeapMediumIcon,
  HeapSmallIcon,
  type IconProps,
} from '../../ui/icons.tsx'

// Sélecteur de Taille de tas [HORS MAQUETTE] (story 1.13) : petit, moyen, grand, boutons
// radio sans présélection. Obligatoire pour envoyer ; une fois choisie, une Taille se
// change mais ne se retire pas. L'option choisie est signalée par une bordure et une coche.

const HEAP_SIZES: readonly {
  value: HeapSize
  icon: ComponentType<IconProps>
  labelKey: `heapSize.${HeapSize}`
  hintKey: `heapSize.${HeapSize}Hint`
}[] = [
  { value: 'small', icon: HeapSmallIcon, labelKey: 'heapSize.small', hintKey: 'heapSize.smallHint' },
  { value: 'medium', icon: HeapMediumIcon, labelKey: 'heapSize.medium', hintKey: 'heapSize.mediumHint' },
  { value: 'large', icon: HeapLargeIcon, labelKey: 'heapSize.large', hintKey: 'heapSize.largeHint' },
]

export function HeapSizePicker({
  value,
  onChange,
  disabled = false,
}: {
  value: HeapSize | undefined
  onChange: (value: HeapSize) => void
  disabled?: boolean
}) {
  const { t } = useTranslation()
  const name = useId()

  return (
    <fieldset disabled={disabled} className="flex min-w-0 flex-col gap-2">
      <legend className="text-lg font-semibold text-brand-900">{t('heapSize.legend')}</legend>
      <div className="grid grid-cols-3 gap-2">
        {HEAP_SIZES.map(({ value: size, icon: SizeIcon, labelKey, hintKey }) => {
          const selected = value === size
          return (
            <label
              key={size}
              className={`relative flex min-h-24 cursor-pointer flex-col items-center justify-center gap-1 rounded-xl border-2 px-2 py-2 text-center text-ink has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-brand-900 ${selected ? 'border-brand-600 bg-mint' : 'border-line bg-surface'}`}
            >
              <input
                type="radio"
                name={name}
                value={size}
                checked={selected}
                onChange={() => onChange(size)}
                className="sr-only"
              />
              {selected && (
                <CheckIcon className="absolute top-1 right-1 size-5 text-brand-600" />
              )}
              <SizeIcon className="size-8 shrink-0 text-brand-600" />
              <span className="font-semibold">{t(labelKey)}</span>
              <span className="text-sm text-muted">{t(hintKey)}</span>
            </label>
          )
        })}
      </div>
    </fieldset>
  )
}
