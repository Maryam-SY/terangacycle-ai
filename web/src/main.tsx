import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import './theme/theme.css'
import i18n from './i18n/index.ts'
import { ensureDeviceId } from './offline/device.ts'
import App from './App.tsx'

document.title = i18n.t('app.name')

// Identifiant d'appareil créé au premier lancement. Jamais journalisé, même en cas
// d'échec (stockage indisponible) : il sera recréé au prochain lancement.
void ensureDeviceId().catch(() => undefined)

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
