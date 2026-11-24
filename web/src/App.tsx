import { useState } from 'react'
import { createBrowserRouter } from 'react-router'
import { RouterProvider } from 'react-router/dom'

import { routes } from './routes.tsx'

export default function App() {
  // Routeur créé au montage, pas à l'import : App.tsx reste importable sous Node.
  const [router] = useState(() => createBrowserRouter(routes))
  return <RouterProvider router={router} />
}
