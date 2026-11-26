import type { RouteObject } from 'react-router'

import { ConsentPage } from './features/consent/ConsentPage.tsx'
import { HomePage } from './features/home/HomePage.tsx'
import { NotFoundPage } from './features/not-found/NotFoundPage.tsx'
import { CapturePage } from './features/report/CapturePage.tsx'
import { ConfirmationPage } from './features/report/ConfirmationPage.tsx'
import { DetailsPage } from './features/report/DetailsPage.tsx'
import { ReportEntry } from './features/report/ReportEntry.tsx'
import { PATHS } from './paths.ts'
import { AppLayout } from './ui/AppLayout.tsx'

// Table des routes, à part d'App.tsx : testable sous Node (App.test.tsx) et sans casser
// le rechargement à chaud (un module de composants n'exporte que des composants).
export const routes: RouteObject[] = [
  {
    // Bandeau « Mode démonstration » au-dessus de tous les écrans (story 2.1).
    element: <AppLayout />,
    children: [
      { path: PATHS.home, element: <HomePage /> },
      { path: PATHS.report, element: <ReportEntry /> },
      { path: PATHS.consent, element: <ConsentPage /> },
      { path: PATHS.capture, element: <CapturePage /> },
      { path: PATHS.details, element: <DetailsPage /> },
      { path: PATHS.confirmation, element: <ConfirmationPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]
