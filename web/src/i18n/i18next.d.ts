// Clés de traduction typées : t('home.titre') est refusé à la compilation.
import 'i18next'

import type { defaultNS, resources } from './index'

declare module 'i18next' {
  interface CustomTypeOptions {
    defaultNS: typeof defaultNS
    resources: (typeof resources)['fr']
  }
}
