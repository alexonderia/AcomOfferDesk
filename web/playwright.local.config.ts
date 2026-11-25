import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './browser-tests',
  outputDir: '../artifacts/br-acom-browser',
  workers: 1,
  timeout: 30_000,
  use: { baseURL: 'http://127.0.0.1:4177', browserName: 'chromium', headless: true },
  projects: [
    { name: 'desktop', use: { viewport: { width: 1440, height: 1000 } } },
    { name: 'mobile', use: { viewport: { width: 390, height: 844 } } },
  ],
  webServer: {
    command: 'npm run build && npm run preview -- --host 127.0.0.1 --port 4177 --strictPort',
    url: 'http://127.0.0.1:4177',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
