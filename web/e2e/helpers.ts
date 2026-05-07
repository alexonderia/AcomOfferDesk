import { expect, type Page, type TestInfo } from '@playwright/test';

const STRICT_CREDENTIALS = process.env.E2E_STRICT_CREDENTIALS === 'true';

export type Credentials = {
  username: string;
  password: string;
};

export const getCredentialsOrSkip = (
  testInfo: TestInfo,
  prefix: 'E2E_SUPERADMIN' | 'E2E_ECONOMIST' | 'E2E_CONTRACTOR'
): Credentials | null => {
  const username = process.env[`${prefix}_USERNAME`]?.trim() ?? '';
  const password = process.env[`${prefix}_PASSWORD`]?.trim() ?? '';

  if (username && password) {
    return { username, password };
  }

  const message = `${prefix}_USERNAME/${prefix}_PASSWORD are not set`;
  if (STRICT_CREDENTIALS) {
    throw new Error(message);
  }

  testInfo.annotations.push({ type: 'skip', description: message });
  return null;
};

export const loginViaKeycloak = async (page: Page, credentials: Credentials): Promise<void> => {
  await page.goto('/login?logged_out=1');

  const loginButton = page.getByRole('button', { name: /войти|login/i });
  if (await loginButton.count()) {
    await loginButton.first().click();
  }

  await page.waitForURL(/\/iam\//, { timeout: 30_000 });

  const usernameInput = page.locator('input[name="username"], input#username').first();
  const passwordInput = page.locator('input[name="password"], input#password').first();
  await usernameInput.fill(credentials.username);
  await passwordInput.fill(credentials.password);

  const submitButton = page.locator('#kc-login, button[type="submit"], input[type="submit"]').first();
  await submitButton.click();

  await page.waitForURL((url) => !url.pathname.startsWith('/iam'), { timeout: 30_000 });
};

export const logoutFromUi = async (page: Page): Promise<void> => {
  const logoutButton = page.getByRole('button', { name: /выйти|logout/i });
  const logoutMenuItem = page.getByRole('menuitem', { name: /выйти|logout/i });

  if (await logoutButton.count()) {
    await logoutButton.first().click();
  } else if (await logoutMenuItem.count()) {
    await logoutMenuItem.first().click();
  } else {
    await page.request.post('/api/v1/auth/logout');
    await page.goto('/login?logged_out=1');
    return;
  }

  await expect(page).toHaveURL(/\/login|\/auth\/login/, { timeout: 20_000 });
};