import { test, expect } from '@playwright/test';

/**
 * Smoke visual mínimo: abre /login, autentica com o admin de dev e confirma que
 * saiu da tela de login (entrou no app). Tira um screenshot do dashboard.
 *
 * Precisa do front em :3000 (o CORS do backend só libera :3000 em dev) e da API
 * em :8000. Credenciais: E2E_EMAIL / E2E_SENHA (defaults = admin do backend/.env).
 */
const EMAIL = process.env.E2E_EMAIL || 'pablo.miguel.dias@gmail.com';
const SENHA = process.env.E2E_SENHA || 'U8OsbLNBD9UCsXiAa1!';

test('login do admin entra no app', async ({ page }) => {
  await page.goto('/login');

  await page.locator('input[type="email"]').fill(EMAIL);
  await page.locator('input[type="password"]').fill(SENHA);
  await page.getByRole('button', { name: /entrar/i }).click();

  // Saiu do /login → autenticou (o app redireciona pra fora da rota pública).
  await expect(page).not.toHaveURL(/\/login/, { timeout: 15_000 });

  await page.screenshot({ path: 'e2e/__screenshots__/pos-login.png', fullPage: true });
});
