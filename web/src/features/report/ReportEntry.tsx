import { Navigate } from 'react-router'

import { PATHS } from '../../paths.ts'
import { useCurrentConsent } from '../consent/useCurrentConsent.ts'

/** Entrée « Signaler un dépôt » (/signaler) : le consentement d'abord s'il manque ou si
 *  son texte a changé, sinon directement l'écran 2 · Capture. */
export function ReportEntry() {
  const accepted = useCurrentConsent()
  if (accepted === undefined) return null
  return <Navigate to={accepted ? PATHS.capture : PATHS.consent} replace />
}
