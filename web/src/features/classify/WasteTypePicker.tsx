import { useId } from 'react'
import { useTranslation } from 'react-i18next'

import type { WasteType } from '../../api/reports.ts'
import { CheckIcon } from '../../ui/icons.tsx'
import { toggleWasteType, WASTE_TYPES, wasteTypeInfo } from './wasteTypes.ts'

// Composant unique des Types de déchet (story 1.13), réutilisé par les epics suivants :
// `WasteTypeBadge` affiche un Type, `WasteTypePicker` en fait choisir un, facultatif.
// Chaque Type : pictogramme dans sa couleur provisoire (`--color-waste-*`), libellé i18n
// en Encre. L'option choisie est signalée par une bordure et une coche, pas seulement par
// la couleur.

/** Type de déchet affiché : pictogramme et libellé. */
export function WasteTypeBadge({ type }: { type: WasteType }) {
  const { t } = useTranslation()
  const { icon: TypeIcon, colorClass, labelKey } = wasteTypeInfo(type)
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-1 text-ink">
      <TypeIcon className={`size-5 shrink-0 ${colorClass}`} />
      <span>{t(labelKey)}</span>
    </span>
  )
}

/** Choix facultatif d'un Type parmi 5 : boutons radio, aucun présélectionné. Toucher le
 *  Type déjà choisi le retire (`onChange(undefined)`). */
export function WasteTypePicker({
  value,
  onChange,
  disabled = false,
}: {
  value: WasteType | undefined
  onChange: (value: WasteType | undefined) => void
  disabled?: boolean
}) {
  const { t } = useTranslation()
  const name = useId()
  const hintId = useId()

  return (
    <fieldset aria-describedby={hintId} disabled={disabled} className="flex min-w-0 flex-col gap-2">
      <legend className="text-lg font-semibold text-brand-900">{t('wasteType.legend')}</legend>
      <p id={hintId} className="text-sm text-muted">
        {t('wasteType.hint')}
      </p>
      <div className="grid grid-cols-2 gap-2">
        {WASTE_TYPES.map(({ value: type, icon: TypeIcon, colorClass, labelKey }) => {
          const selected = value === type
          return (
            <label
              key={type}
              className={`relative flex min-h-14 cursor-pointer items-center gap-3 rounded-xl border-2 px-3 py-2 text-ink has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-brand-900 ${selected ? 'border-brand-600 bg-mint' : 'border-line bg-surface'}`}
            >
              <input
                type="radio"
                name={name}
                value={type}
                checked={selected}
                onChange={() => onChange(type)}
                // Toucher l'option déjà choisie ne déclenche pas `change` : elle est retirée ici.
                onClick={() => {
                  if (selected) onChange(toggleWasteType(value, type))
                }}
                className="sr-only"
              />
              <TypeIcon className={`size-7 shrink-0 ${colorClass}`} />
              <span className="min-w-0 flex-1 font-medium">{t(labelKey)}</span>
              {selected && <CheckIcon className="size-6 shrink-0 text-brand-600" />}
            </label>
          )
        })}
      </div>
    </fieldset>
  )
}
