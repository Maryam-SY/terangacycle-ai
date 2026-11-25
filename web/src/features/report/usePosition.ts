// Suivi de la Position de l'appareil (story 1.8) : `watchPosition` en haute précision,
// arrêté au démontage de l'écran, relancé par « Réessayer ».
// Donnée personnelle : les coordonnées ne sont jamais écrites dans la console ni envoyées
// ici ; elles ne servent qu'à l'affichage et à la vérification de la Zone active.
import { useCallback, useEffect, useRef, useState } from 'react'

export type PositionState =
  | { status: 'locating' }
  /** `fixedAt` : heure de la mesure (ms depuis l'époque, horloge de l'appareil). */
  | { status: 'located'; lat: number; lng: number; accuracy: number; fixedAt: number }
  | { status: 'error'; reason: 'denied' | 'unavailable' }

/** Options de `watchPosition` : GPS demandé, aucune position en cache, 30 s par mesure. */
export const WATCH_OPTIONS: PositionOptions = {
  enableHighAccuracy: true,
  maximumAge: 0,
  timeout: 30_000,
}

const PERMISSION_DENIED = 1
/** Âge maximal d'une Position gardée malgré une mesure manquée (délai, signal perdu). */
export const MAX_FIX_AGE_MS = 60_000

/** État après une erreur de `watchPosition`. Un refus efface toujours la Position ; une
 *  mesure manquée garde la dernière Position si elle a moins de `MAX_FIX_AGE_MS`. */
export function afterPositionError(
  current: PositionState,
  code: number,
  now: number,
): PositionState {
  if (code === PERMISSION_DENIED) return { status: 'error', reason: 'denied' }
  if (current.status === 'located' && now - current.fixedAt < MAX_FIX_AGE_MS) return current
  return { status: 'error', reason: 'unavailable' }
}

const UNAVAILABLE: PositionState = { status: 'error', reason: 'unavailable' }

/** État de la Position, `retry()` pour relancer le suivi après un refus ou un échec, et
 *  `current()` : la dernière mesure reçue, même si l'écran n'a pas encore été redessiné
 *  (une photo peut arriver juste après une nouvelle mesure). */
export function usePosition(): {
  position: PositionState
  retry: () => void
  current: () => PositionState
} {
  const [position, setPosition] = useState<PositionState>({ status: 'locating' })
  const latest = useRef<PositionState>({ status: 'locating' })
  const update = useCallback((next: PositionState) => {
    latest.current = next
    setPosition(next)
  }, [])
  // Chaque essai relance l'effet : nouveau `watchPosition`, l'ancien est arrêté.
  const [attempt, setAttempt] = useState(0)
  const geolocation = typeof navigator === 'undefined' ? undefined : navigator.geolocation

  useEffect(() => {
    if (!geolocation) return undefined
    let active = true
    const watchId = geolocation.watchPosition(
      ({ coords }) => {
        if (!active) return
        update({
          status: 'located',
          lat: coords.latitude,
          lng: coords.longitude,
          accuracy: coords.accuracy,
          fixedAt: Date.now(),
        })
      },
      (error) => {
        if (!active) return
        update(afterPositionError(latest.current, error.code, Date.now()))
      },
      WATCH_OPTIONS,
    )
    return () => {
      active = false
      geolocation.clearWatch(watchId)
    }
  }, [geolocation, attempt, update])

  const retry = useCallback(() => {
    update({ status: 'locating' })
    setAttempt((value) => value + 1)
  }, [update])

  const current = useCallback(
    () => (geolocation ? latest.current : UNAVAILABLE),
    [geolocation],
  )

  // Navigateur sans géolocalisation : rien à suivre, l'écran l'explique.
  if (!geolocation) return { position: UNAVAILABLE, retry, current }
  return { position, retry, current }
}
