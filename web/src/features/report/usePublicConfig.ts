import { useCallback, useEffect, useState } from 'react'

import { loadPublicConfig } from '../../offline/publicConfig.ts'
import type { ConfigState } from './capture.ts'

/** Configuration publique (Zone active, seuil de précision) : celle gardée sur l'appareil
 *  tout de suite, mise à jour quand la lecture réseau en arrière-plan aboutit ; sans
 *  configuration gardée, lecture réseau. `retry()` relance la lecture (« Réessayer »). */
export function usePublicConfig(): { config: ConfigState; retry: () => void } {
  const [config, setConfig] = useState<ConfigState>({ status: 'loading' })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let active = true
    loadPublicConfig().then(
      ({ config: loaded, refreshed }) => {
        if (!active) return
        setConfig({ status: 'ready', config: loaded })
        void refreshed?.then((fresh) => {
          if (active && fresh) setConfig({ status: 'ready', config: fresh })
        })
      },
      () => {
        if (active) setConfig({ status: 'unavailable' })
      },
    )
    return () => {
      active = false
    }
  }, [attempt])

  const retry = useCallback(() => {
    setConfig({ status: 'loading' })
    setAttempt((value) => value + 1)
  }, [])

  return { config, retry }
}
