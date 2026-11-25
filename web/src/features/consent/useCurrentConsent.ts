import { useEffect, useState } from 'react'

import { hasCurrentConsent } from './consent.ts'

/** Délai maximal de lecture de `meta` : une base bloquée ne laisse pas un écran vide. */
export const CONSENT_READ_TIMEOUT_MS = 3000

/** `undefined` pendant la lecture de `meta`, puis vrai si la version courante du
 *  consentement est acceptée. Une base illisible, ou qui ne répond pas dans le délai, vaut
 *  « pas de consentement » : le Citoyen revoit l'écran de consentement plutôt qu'un écran
 *  vide. */
export function useCurrentConsent(): boolean | undefined {
  const [accepted, setAccepted] = useState<boolean>()

  useEffect(() => {
    let active = true
    let timer: ReturnType<typeof setTimeout> | undefined
    const timeout = new Promise<boolean>((resolve) => {
      timer = setTimeout(() => resolve(false), CONSENT_READ_TIMEOUT_MS)
    })
    void Promise.race([hasCurrentConsent().catch(() => false), timeout]).then((value) => {
      clearTimeout(timer)
      if (active) setAccepted(value)
    })
    return () => {
      active = false
      clearTimeout(timer)
    }
  }, [])

  return accepted
}
