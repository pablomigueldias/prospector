import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright mínimo — smoke visual do front (login + screenshot).
 *
 * Pré-requisitos (uma vez): `npm i -D @playwright/test && npx playwright install chromium`.
 * Rodar: API em :8000 + front em :3000 no ar, então `npm run e2e`.
 * Credenciais via env (E2E_EMAIL / E2E_SENHA) ou os defaults do backend/.env de dev.
 *
 * Cobre o §6 do MELHORIAS (verificação visual). Ver docs/ORGANIZACAO_REFATORACAO.md.
 */
export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  expect: { timeout: 10_000 },
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:3000',
    screenshot: 'only-on-failure',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
