import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

import fr from './fr.json'
// Mêmes clés que fr.json ; valeurs encore en français, à traduire par des locuteurs natifs.
import wo from './wo.json'

export const defaultNS = 'translation'
export const resources = {
  fr: { translation: fr },
  wo: { translation: wo },
} as const

void i18n.use(initReactI18next).init({
  resources,
  lng: 'fr',
  fallbackLng: 'fr',
  supportedLngs: ['fr', 'wo'],
  defaultNS,
  // Ressources en ligne : initialisation synchrone, t() est prêt dès l'import.
  initAsync: false,
  // React échappe déjà le texte rendu.
  interpolation: { escapeValue: false },
})

// L'attribut lang de la page suit la langue choisie (lecteurs d'écran, césure).
// document n'existe pas sous Node (tests Vitest).
i18n.on('languageChanged', (lng) => {
  if (typeof document !== 'undefined') document.documentElement.lang = lng
})

export default i18n
