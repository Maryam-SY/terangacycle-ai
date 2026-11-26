import { useId, type ComponentType } from 'react'
import { useTranslation } from 'react-i18next'

import {
  CheckIcon,
  FlagIcon,
  PhotoCheckIcon,
  ShieldCheckIcon,
  TruckIcon,
  type IconProps,
} from '../../ui/icons.tsx'

// Frise de suivi (story 1.13, complétée par la story 4.7 : état « rejeté », date des
// étapes) : les 4 étapes du traitement d'un Signalement en liste ordonnée, chacune avec
// pictogramme et libellé. L'étape actuelle est annoncée (`aria-current="step"`) et
// distinguée autrement que par la couleur : coche, libellé en gras et mention visible.

export type TimelineStep = 'reported' | 'validated' | 'assigned' | 'collected'

const STEPS: readonly { step: TimelineStep; icon: ComponentType<IconProps> }[] = [
  { step: 'reported', icon: FlagIcon },
  { step: 'validated', icon: ShieldCheckIcon },
  { step: 'assigned', icon: TruckIcon },
  { step: 'collected', icon: PhotoCheckIcon },
]

export function TrackingTimeline({ current }: { current: TimelineStep }) {
  const { t } = useTranslation()
  const titleId = useId()

  return (
    <section aria-labelledby={titleId} className="flex flex-col gap-3">
      <h2 id={titleId} className="text-lg font-semibold text-brand-900">
        {t('timeline.title')}
      </h2>
      <ol className="flex flex-col gap-2">
        {STEPS.map(({ step, icon: StepIcon }) => {
          const isCurrent = step === current
          return (
            <li
              key={step}
              aria-current={isCurrent ? 'step' : undefined}
              className={`flex items-center gap-3 rounded-xl border-2 px-3 py-2 ${isCurrent ? 'border-brand-600 bg-mint' : 'border-line bg-surface'}`}
            >
              <StepIcon className="size-6 shrink-0 text-brand-600" />
              <span className={`min-w-0 flex-1 text-ink ${isCurrent ? 'font-bold' : ''}`}>
                {t(`timeline.${step}`)}
              </span>
              {isCurrent && (
                <span className="flex shrink-0 items-center gap-1 text-sm font-semibold text-brand-900">
                  <CheckIcon className="size-5 text-brand-600" />
                  {t('timeline.current')}
                </span>
              )}
            </li>
          )
        })}
      </ol>
    </section>
  )
}
