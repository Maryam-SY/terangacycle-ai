import type { RouteObject } from 'react-router'

import { HomePage } from './features/home/HomePage.tsx'
import { NotFoundPage } from './features/not-found/NotFoundPage.tsx'

// Table des routes, à part d'App.tsx : testable sous Node (App.test.tsx) et sans casser
// le rechargement à chaud (un module de composants n'exporte que des composants).
export const routes: RouteObject[] = [
  { path: '/', element: <HomePage /> },
  { path: '*', element: <NotFoundPage /> },
]
