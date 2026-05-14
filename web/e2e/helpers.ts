import { expect, type Page, type TestInfo } from '@playwright/test';

const STRICT_CREDENTIALS = process.env.E2E_STRICT_CREDENTIALS === 'true';

export type Credentials = {
  username: string;
  password: string;
};

export const getCredentialsOrSkip = (
  testInfo: TestInfo,
  prefix:
    | 'E2E_SUPERADMIN'
    | 'E2E_ADMIN'
    | 'E2E_PROJECT_MANAGER'
    | 'E2E_LEAD_ECONOMIST'
    | 'E2E_ECONOMIST'
    | 'E2E_OPERATOR'
    | 'E2E_CONTRACTOR'
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
  const waitForPostLoginUrl = async (): Promise<void> => {
    await page.waitForURL(
      (url) =>
        !url.pathname.startsWith('/iam') &&
        !url.pathname.startsWith('/api/v1/auth/oidc/login') &&
        !url.pathname.startsWith('/auth/callback') &&
        !url.pathname.startsWith('/api/v1/auth/callback'),
      { timeout: 30_000, waitUntil: 'domcontentloaded' }
    );
  };

  await page.goto('/api/v1/auth/oidc/login?next_path=%2F&force_prompt=1');

  const visitSiteButton = page.getByRole('button', { name: /visit site/i });
  if (await visitSiteButton.isVisible({ timeout: 3_000 }).catch(() => false)) {
    await visitSiteButton.click();
  }

  const usernameInput = page.locator('input[name="username"], input#username').first();
  const passwordInput = page.locator('input[name="password"], input#password').first();
  await usernameInput.waitFor({ state: 'visible', timeout: 30_000 });
  await usernameInput.fill(credentials.username);
  await passwordInput.fill(credentials.password);

  const submitButton = page.locator('#kc-login, button[type="submit"], input[type="submit"]').first();
  await submitButton.click();

  try {
    await waitForPostLoginUrl();
  } catch (error) {
    if (new URL(page.url()).pathname.startsWith('/iam')) {
      await submitButton.click();
      await waitForPostLoginUrl();
    } else {
      throw error;
    }
  }

  const currentUrl = new URL(page.url());
  if (currentUrl.pathname === '/login' && currentUrl.searchParams.has('auth_error')) {
    throw new Error(`Login failed with auth_error=${currentUrl.searchParams.get('auth_error')}`);
  }
};

export const logoutFromUi = async (page: Page): Promise<void> => {
  const logoutButton = page.getByRole('button', { name: /выйти|logout/i });
  const logoutMenuItem = page.getByRole('menuitem', { name: /выйти|logout/i });

  if (await logoutButton.count()) {
    await logoutButton.first().click();
    await page.waitForLoadState('domcontentloaded');
    return;
  }

  if (await logoutMenuItem.count()) {
    await logoutMenuItem.first().click();
    await page.waitForLoadState('domcontentloaded');
    return;
  }

  try {
    await page.request.post('/api/v1/auth/logout', { failOnStatusCode: false });
  } catch {
    // ngrok/public tunnel can reset connection during logout; cookie cleanup is sufficient for test isolation.
  }
  await page.context().clearCookies();
};

export const assertNoSevereConsoleErrors = async (
  page: Page,
  action: () => Promise<void>
): Promise<void> => {
  const severeErrors: string[] = [];
  const listener = (msg: { type: () => string; text: () => string }) => {
    if (msg.type() !== 'error') {
      return;
    }

    const text = msg.text();
    if (text.includes('the server responded with a status of 401')) {
      return;
    }

    severeErrors.push(text);
  };

  page.on('console', listener);
  try {
    await action();
  } finally {
    page.off('console', listener);
  }

  expect(severeErrors, `Console errors: ${severeErrors.join('\n')}`).toEqual([]);
};
