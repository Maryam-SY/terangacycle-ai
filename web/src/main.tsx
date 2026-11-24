import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import './theme/theme.css'
import i18n from './i18n/index.ts'
import App from './App.tsx'

document.title = i18n.t('app.name')

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
