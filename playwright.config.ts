import { defineConfig } from '@playwright/test';
import { existsSync } from 'node:fs';

export default defineConfig({
  testDir: './e2e',
  timeout: 90_000,
  expect: { timeout: 10_000 },
  workers: 1,
  reporter: [['list'], ['html', { open: 'never' }], ['json', { outputFile: 'artifacts/e2e-results.json' }]],
  use: {
    baseURL: 'http://127.0.0.1:8011',
    viewport: { width: 1512, height: 1050 },
    channel: existsSync('/Applications/Google Chrome.app') ? 'chrome' : undefined,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: '.venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port 8011',
    url: 'http://127.0.0.1:8011/api/health',
    reuseExistingServer: false,
    env: { ESTIMATOR_DB: `artifacts/e2e-${Date.now()}.sqlite3` },
    timeout: 30_000,
  },
});
