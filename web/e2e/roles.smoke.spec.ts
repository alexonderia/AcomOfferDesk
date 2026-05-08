import { expect, test, type Page } from '@playwright/test';
import { getCredentialsOrSkip, loginViaKeycloak, logoutFromUi } from './helpers';

type RoleScenario = {
  name: string;
  envPrefix:
    | 'E2E_SUPERADMIN'
    | 'E2E_ADMIN'
    | 'E2E_PROJECT_MANAGER'
    | 'E2E_LEAD_ECONOMIST'
    | 'E2E_ECONOMIST'
    | 'E2E_OPERATOR'
    | 'E2E_CONTRACTOR';
  canAccessAdmin: boolean;
  canAccessDashboard: boolean;
  canAccessFeedback: boolean;
};

const scenarios: RoleScenario[] = [
  { name: 'superadmin', envPrefix: 'E2E_SUPERADMIN', canAccessAdmin: true, canAccessDashboard: true, canAccessFeedback: true },
  { name: 'admin', envPrefix: 'E2E_ADMIN', canAccessAdmin: true, canAccessDashboard: false, canAccessFeedback: false },
  {
    name: 'project_manager',
    envPrefix: 'E2E_PROJECT_MANAGER',
    canAccessAdmin: true,
    canAccessDashboard: true,
    canAccessFeedback: false
  },
  {
    name: 'lead_economist',
    envPrefix: 'E2E_LEAD_ECONOMIST',
    canAccessAdmin: true,
    canAccessDashboard: true,
    canAccessFeedback: false
  },
  { name: 'economist', envPrefix: 'E2E_ECONOMIST', canAccessAdmin: true, canAccessDashboard: false, canAccessFeedback: false },
  { name: 'operator', envPrefix: 'E2E_OPERATOR', canAccessAdmin: false, canAccessDashboard: false, canAccessFeedback: false },
  { name: 'contractor', envPrefix: 'E2E_CONTRACTOR', canAccessAdmin: false, canAccessDashboard: false, canAccessFeedback: false }
];

const assertRouteAccess = async (
  page: Page,
  args: {
    path: string;
    shouldAllow: boolean;
  }
): Promise<void> => {
  const { path, shouldAllow } = args;
  await page.goto(path);
  await page.waitForLoadState('networkidle');

  const pathname = new URL(page.url()).pathname;
  if (shouldAllow) {
    expect(pathname).toBe(path);
    return;
  }

  expect(pathname, `Route '${path}' should be denied`).not.toBe(path);
  expect(pathname).toMatch(/^\/(requests|admin|pm-dashboard|account|login|auth\/login)/);
};

for (const scenario of scenarios) {
  test(`${scenario.name} role routes smoke @smoke`, async ({ page }, testInfo) => {
    const credentials = getCredentialsOrSkip(testInfo, scenario.envPrefix);
    test.skip(!credentials, `Missing ${scenario.envPrefix} credentials`);

    await loginViaKeycloak(page, credentials!);
    await expect(page).toHaveURL(/\/(requests|admin|pm-dashboard|auth\/callback)/);

    await assertRouteAccess(page, { path: '/requests', shouldAllow: true });
    await assertRouteAccess(page, { path: '/admin', shouldAllow: scenario.canAccessAdmin });
    await assertRouteAccess(page, { path: '/pm-dashboard', shouldAllow: scenario.canAccessDashboard });
    await assertRouteAccess(page, { path: '/feedback', shouldAllow: scenario.canAccessFeedback });

    await logoutFromUi(page);
  });
}
