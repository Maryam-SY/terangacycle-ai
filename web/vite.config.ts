import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

import {
  BACKGROUND_COLOR,
  NAVIGATE_FALLBACK_DENYLIST,
  PRECACHE_GLOB_PATTERNS,
  THEME_COLOR,
} from './pwa.config.ts'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'TerangaCycle AI',
        short_name: 'TerangaCycle',
        lang: 'fr',
        start_url: '/',
        scope: '/',
        display: 'standalone',
        theme_color: THEME_COLOR,
        background_color: BACKGROUND_COLOR,
        icons: [
          { src: '/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icon-512.png', sizes: '512x512', type: 'image/png' },
        ],
      },
      workbox: {
        globPatterns: PRECACHE_GLOB_PATTERNS,
        navigateFallbackDenylist: NAVIGATE_FALLBACK_DENYLIST,
      },
    }),
  ],
})
