import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

// Backend al que el servidor de desarrollo reenvía /api, /admin y /media.
const BACKEND = process.env.VITE_BACKEND_URL ?? 'http://localhost:8000'
const TILES = 'tile.openstreetmap.org'

export default defineConfig({
  plugins: [
    react(),
    // PWA: instalable y con caché para conexiones débiles (sección 4 y 8).
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['icon.svg'],
      manifest: {
        name: 'Mapa Comunitario de Puntos de Carga',
        short_name: 'Puntos de Carga',
        description: 'Encuentra lugares cercanos con corriente para cargar tus equipos.',
        lang: 'es',
        start_url: '/',
        display: 'standalone',
        background_color: '#0f172a',
        theme_color: '#0f172a',
        icons: [
          { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        navigateFallbackDenylist: [/^\/api/, /^\/admin/, /^\/media/],
        runtimeCaching: [
          {
            // Losetas del mapa: primero caché. Las que ya viste se ven sin conexión.
            urlPattern: ({ url }) => url.hostname.endsWith(TILES),
            handler: 'CacheFirst',
            options: {
              cacheName: 'losetas-mapa',
              expiration: { maxEntries: 800, maxAgeSeconds: 60 * 60 * 24 * 30 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            // Consultas de puntos: primero red; si no hay, la última respuesta guardada.
            urlPattern: ({ url }) => url.pathname.startsWith('/api/puntos'),
            handler: 'NetworkFirst',
            method: 'GET',
            options: {
              cacheName: 'api-puntos',
              networkTimeoutSeconds: 5,
              expiration: { maxEntries: 60, maxAgeSeconds: 60 * 60 * 24 },
            },
          },
        ],
      },
    }),
  ],
  server: {
    port: 5173,
    proxy: {
      '/api': BACKEND,
      '/admin': BACKEND,
      '/media': BACKEND,
      '/static': BACKEND,
    },
  },
  preview: {
    proxy: {
      '/api': BACKEND,
      '/media': BACKEND,
    },
  },
})
