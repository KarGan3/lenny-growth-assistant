import { defineConfig } from '@playwright/test'
export default defineConfig({
  testDir: './browser-tests',
  timeout: 30000,
  workers: 1,
  use: {
    baseURL: process.env.EVALUATION_UI_URL || 'http://127.0.0.1:5173',
    viewport: { width: 1440, height: 900 },
    launchOptions: { executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome' },
  },
})
