import { defineConfig, devices } from '@playwright/test'

/**
 * Prueba del flujo completo (sección 9): buscar, abrir ficha, reportar estado.
 * Requiere el backend en marcha con datos de demo (`python manage.py sembrar_demo`).
 */
export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:4173',
    // Teléfono de gama media: así probamos el diseño móvil.
    ...devices['Pixel 5'],
    geolocation: { latitude: 22.4067, longitude: -79.9646 }, // centro de Santa Clara
    permissions: ['geolocation'],
    locale: 'es-ES',
    timezoneId: 'America/Havana',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    launchOptions: process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {},
  },
  webServer: process.env.E2E_BASE_URL
    ? undefined
    : { command: 'npm run build && npm run preview', port: 4173, reuseExistingServer: true, timeout: 120_000 },
})
