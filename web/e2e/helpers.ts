import { expect, type Page, type TestInfo } from '@playwright/test';

const STRICT_CREDENTIALS = process.env.E2E_STRICT_CREDENTIALS === 'true';

export type Credentials = {
  username: string;
  password: string;
};

const TRANSIENT_NAVIGATION_ERRORS = [
  'ERR_CONNECTION_CLOSED',
  'ERR_CONNECTION_RESET',
  'ERR_TUNNEL_CONNECTION_FAILED',
  'ERR_NETWORK_CHANGED',
  'ERR_TIMED_OUT',
  'ERR_NGROK_3200',
];

const isTransientNavigationError = (error: unknown): boolean => {
  const message = error instanceof Error ? error.message : String(error);
  return TRANSIENT_NAVIGATION_ERRORS.some((fragment) => message.includes(fragment));
};

export const bypassNgrokInterstitialIfPresent = async (page: Page): Promise<void> => {
  const visitSiteButton = page.getByRole('button', { name: /visit site/i });
  if (await visitSiteButton.isVisible({ timeout: 3_000 }).catch(() => false)) {
    await visitSiteButton.click();
  }
};

const isNgrokEndpointOfflinePage = async (page: Page): Promise<boolean> => {
  const offlineHeading = page.getByRole('heading', { name: /ERR_NGROK_3200/i });
  return offlineHeading.isVisible({ timeout: 1_000 }).catch(() => false);
};

export const gotoWithRetry = async (
  page: Page,
  url: string,
  options: { attempts?: number; timeoutMs?: number; waitUntil?: 'load' | 'domcontentloaded' | 'networkidle' | 'commit' } = {}
): Promise<void> => {
  const attempts = options.attempts ?? 4;
  const timeoutMs = options.timeoutMs ?? 30_000;
  const waitUntil = options.waitUntil ?? 'domcontentloaded';

  let lastError: unknown = null;
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      await page.goto(url, { timeout: timeoutMs, waitUntil });
      await bypassNgrokInterstitialIfPresent(page);
      if (await isNgrokEndpointOfflinePage(page)) {
        throw new Error('ERR_NGROK_3200 endpoint offline');
      }
      return;
    } catch (error) {
      lastError = error;
      if (attempt >= attempts || !isTransientNavigationError(error)) {
        throw error;
      }
      await page.waitForTimeout(600 * attempt);
    }
  }

  throw lastError instanceof Error ? lastError : new Error(`Navigation failed for ${url}`);
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
  const loginUrl = '/api/v1/auth/oidc/login?next_path=%2F&force_prompt=1';

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

  const usernameInput = page.locator('input[name="username"], input#username').first();
  const passwordInput = page.locator('input[name="password"], input#password').first();
  const submitButton = page.locator('#kc-login, button[type="submit"], input[type="submit"]').first();

  for (let attempt = 1; attempt <= 3; attempt += 1) {
    await gotoWithRetry(page, loginUrl, {
      attempts: 5,
      waitUntil: 'domcontentloaded',
    });

    const loginFormVisible = await usernameInput
      .waitFor({ state: 'visible', timeout: 30_000 })
      .then(() => true)
      .catch(() => false);

    if (!loginFormVisible) {
      if (attempt >= 3) {
        throw new Error(`Keycloak login form is not visible after ${attempt} attempts (url: ${page.url()})`);
      }
      await page.waitForTimeout(1_000 * attempt);
      continue;
    }

    await usernameInput.fill(credentials.username);
    await passwordInput.fill(credentials.password);
    await submitButton.click();

    try {
      await waitForPostLoginUrl();
      break;
    } catch (error) {
      const currentPath = new URL(page.url()).pathname;
      if (attempt >= 3 || !currentPath.startsWith('/iam')) {
        throw error;
      }
      await page.waitForTimeout(1_000 * attempt);
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
  const isIgnorableTransientResourceError = (text: string): boolean =>
    text.startsWith('Failed to load resource: net::') &&
    (text.includes('ERR_CONNECTION_CLOSED') ||
      text.includes('ERR_CONNECTION_RESET') ||
      text.includes('ERR_TUNNEL_CONNECTION_FAILED') ||
      text.includes('ERR_NETWORK_CHANGED') ||
      text.includes('ERR_TIMED_OUT'));

  const listener = (msg: { type: () => string; text: () => string }) => {
    if (msg.type() !== 'error') {
      return;
    }

    const text = msg.text();
    if (text.includes('the server responded with a status of 401')) {
      return;
    }
    if (isIgnorableTransientResourceError(text)) {
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
