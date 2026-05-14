import { expect, test } from '@playwright/test';
import { assertNoSevereConsoleErrors, getCredentialsOrSkip, loginViaKeycloak, logoutFromUi } from './helpers';

const dashboardScenarios = [
  { name: 'project_manager', envPrefix: 'E2E_PROJECT_MANAGER' as const },
  { name: 'lead_economist', envPrefix: 'E2E_LEAD_ECONOMIST' as const },
];

for (const scenario of dashboardScenarios) {
  test(`${scenario.name} dashboard navigation and filters @dashboard`, async ({ page }, testInfo) => {
    const credentials = getCredentialsOrSkip(testInfo, scenario.envPrefix);
    test.skip(!credentials, `Missing ${scenario.envPrefix} credentials`);

    await loginViaKeycloak(page, credentials!);

    for (const path of ['/pm-dashboard', '/pm-dashboard/savings', '/pm-dashboard/plan']) {
      await assertNoSevereConsoleErrors(page, async () => {
        await page.goto(path);
        await page.waitForLoadState('networkidle');
      });
      await expect(page).toHaveURL(new RegExp(path.replace('/', '\\/')));
      await expect(page.locator('main')).toBeVisible();
      const bodyText = await page.locator('body').innerText();
      expect(bodyText).not.toMatch(/\bNaN\b|undefined/);
    }

    await page.goto('/pm-dashboard/savings');
    await page.waitForLoadState('networkidle');
    const dateInputs = page.locator('input[type="date"]');
    if ((await dateInputs.count()) >= 2) {
      await dateInputs.nth(0).fill('2099-01-01');
      await dateInputs.nth(1).fill('2099-01-31');
      await expect(page.locator('body')).toContainText(
        /\u043d\u0435\u0442 \u0437\u0430\u044f\u0432\u043e\u043a|\u043f\u043e\u043a\u0430 \u043d\u0435\u0442/i
      );
    }

    await logoutFromUi(page);
  });
}
