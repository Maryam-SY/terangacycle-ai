import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import { defineConfig } from 'vitest/config'

import { MANIFEST, NAVIGATE_FALLBACK_DENYLIST, PRECACHE_GLOB_PATTERNS } from './pwa.config.ts'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        ...MANIFEST,
        icons: MANIFEST.icons.map((icon) => ({ ...icon })),
      },
      workbox: {
        globPatterns: PRECACHE_GLOB_PATTERNS,
        navigateFallbackDenylist: NAVIGATE_FALLBACK_DENYLIST,
      },
    }),
  ],
  test: {
    // Vitest seulement : les parcours Playwright (e2e/*.spec.ts) tournent à part (npm run test:e2e).
    include: ['src/**/*.test.{ts,tsx}'],
  },
})
