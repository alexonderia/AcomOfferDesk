import { expect, test, type Page } from '@playwright/test';
import { assertNoSevereConsoleErrors, getCredentialsOrSkip, loginViaKeycloak, logoutFromUi } from './helpers';

type RolePrefix =
  | 'E2E_SUPERADMIN'
  | 'E2E_ADMIN'
  | 'E2E_PROJECT_MANAGER'
  | 'E2E_LEAD_ECONOMIST'
  | 'E2E_ECONOMIST'
  | 'E2E_OPERATOR'
  | 'E2E_CONTRACTOR';

type RouteExpectation = {
  path: string;
  markerRegex?: RegExp;
};

type RoleScenario = {
  name: string;
  envPrefix: RolePrefix;
  allowedRoutes: RouteExpectation[];
  forbiddenRoutes: string[];
};

const scenarios: RoleScenario[] = [
  {
    name: 'superadmin',
    envPrefix: 'E2E_SUPERADMIN',
    allowedRoutes: [
      { path: '/requests', markerRegex: /\u0417\u0430\u044f\u0432\u043a/i },
      { path: '/admin', markerRegex: /\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b/i },
      { path: '/pm-dashboard', markerRegex: /\u0421\u043e\u0442\u0440\u0443\u0434\u043d|dashboard/i },
      { path: '/feedback', markerRegex: /\u041e\u0431\u0440\u0430\u0442\u043d|feedback/i },
    ],
    forbiddenRoutes: [],
  },
  {
    name: 'admin',
    envPrefix: 'E2E_ADMIN',
    allowedRoutes: [{ path: '/admin', markerRegex: /\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b/i }],
    forbiddenRoutes: ['/requests', '/pm-dashboard', '/feedback'],
  },
  {
    name: 'project_manager',
    envPrefix: 'E2E_PROJECT_MANAGER',
    allowedRoutes: [
      { path: '/requests', markerRegex: /\u0417\u0430\u044f\u0432\u043a/i },
      { path: '/admin', markerRegex: /\u042d\u043a\u043e\u043d\u043e\u043c|\u0421\u043e\u0442\u0440\u0443\u0434\u043d/i },
      { path: '/pm-dashboard', markerRegex: /\u041d\u0435\u0440\u0430\u0441\u043f\u0440\u0435\u0434|\u0421\u043e\u0442\u0440\u0443\u0434\u043d/i },
    ],
    forbiddenRoutes: ['/feedback'],
  },
  {
    name: 'lead_economist',
    envPrefix: 'E2E_LEAD_ECONOMIST',
    allowedRoutes: [
      { path: '/requests', markerRegex: /\u0417\u0430\u044f\u0432\u043a/i },
      { path: '/admin', markerRegex: /\u042d\u043a\u043e\u043d\u043e\u043c|\u041f\u043e\u043b\u044c\u0437/i },
      { path: '/pm-dashboard', markerRegex: /\u041d\u0435\u0440\u0430\u0441\u043f\u0440\u0435\u0434|\u0421\u043e\u0442\u0440\u0443\u0434\u043d/i },
    ],
    forbiddenRoutes: ['/feedback'],
  },
  {
    name: 'economist',
    envPrefix: 'E2E_ECONOMIST',
    allowedRoutes: [
      { path: '/requests', markerRegex: /\u0417\u0430\u044f\u0432\u043a/i },
      { path: '/admin', markerRegex: /\u042d\u043a\u043e\u043d\u043e\u043c|\u041f\u043e\u043b\u044c\u0437/i },
    ],
    forbiddenRoutes: ['/pm-dashboard', '/feedback'],
  },
  {
    name: 'operator',
    envPrefix: 'E2E_OPERATOR',
    allowedRoutes: [{ path: '/requests', markerRegex: /\u0417\u0430\u044f\u0432\u043a/i }],
    forbiddenRoutes: ['/admin', '/pm-dashboard', '/feedback'],
  },
  {
    name: 'contractor',
    envPrefix: 'E2E_CONTRACTOR',
    allowedRoutes: [{ path: '/requests', markerRegex: /\u0417\u0430\u044f\u0432\u043a/i }],
    forbiddenRoutes: ['/admin', '/pm-dashboard', '/feedback'],
  },
];

const assertAllowedRoute = async (page: Page, expectation: RouteExpectation): Promise<void> => {
  await assertNoSevereConsoleErrors(page, async () => {
    await page.goto(expectation.path);
    await page.waitForLoadState('networkidle');
  });

  const pathname = new URL(page.url()).pathname;
  expect(pathname, `Route '${expectation.path}' should be allowed`).toBe(expectation.path);
  await expect(page.locator('main')).toBeVisible();

  if (expectation.markerRegex) {
    await expect(page.getByText(expectation.markerRegex).first()).toBeVisible();
  }
};

const assertForbiddenRoute = async (page: Page, path: string): Promise<void> => {
  await assertNoSevereConsoleErrors(page, async () => {
    await page.goto(path);
    await page.waitForLoadState('networkidle');
  });

  const pathname = new URL(page.url()).pathname;
  expect(pathname, `Route '${path}' should be denied`).not.toBe(path);
  expect(pathname).toMatch(/^\/(requests|admin|pm-dashboard|account|login|auth\/login)/);
};

for (const scenario of scenarios) {
  test(`${scenario.name} route matrix @roles`, async ({ page }, testInfo) => {
    const credentials = getCredentialsOrSkip(testInfo, scenario.envPrefix);
    test.skip(!credentials, `Missing ${scenario.envPrefix} credentials`);

    await loginViaKeycloak(page, credentials!);
    await expect(page).toHaveURL(/\/(requests|admin|pm-dashboard|account|auth\/callback)/);

    for (const route of scenario.allowedRoutes) {
      await assertAllowedRoute(page, route);
    }

    for (const forbiddenRoute of scenario.forbiddenRoutes) {
      await assertForbiddenRoute(page, forbiddenRoute);
    }

    await logoutFromUi(page);
  });
}
