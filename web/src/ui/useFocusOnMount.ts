import { useCallback } from 'react'

/** Ref à poser sur le `<h1 tabIndex={-1}>` d'un écran : le focus y est placé dès que le
 *  titre apparaît (y compris après une attente, comme sur la capture), pour que les
 *  lecteurs d'écran annoncent le changement d'écran après une navigation côté client. */
export function useFocusOnMount<T extends HTMLElement>() {
  return useCallback((element: T | null) => {
    element?.focus()
  }, [])
}
