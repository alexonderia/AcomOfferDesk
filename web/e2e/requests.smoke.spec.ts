import { expect, test } from '@playwright/test';
import { assertNoSevereConsoleErrors, getCredentialsOrSkip, gotoWithRetry, loginViaKeycloak, logoutFromUi } from './helpers';

test('economist requests smoke @smoke', async ({ page }, testInfo) => {
  const credentials = getCredentialsOrSkip(testInfo, 'E2E_ECONOMIST');
  test.skip(!credentials, 'Missing economist credentials');

  await loginViaKeycloak(page, credentials!);

  await assertNoSevereConsoleErrors(page, async () => {
    await gotoWithRetry(page, '/requests');
    await expect(page).toHaveURL(/\/requests/);
    await page.waitForLoadState('networkidle');
  });

  await expect(page.locator('main')).toBeVisible();
  await logoutFromUi(page);
});

test('contractor requests smoke @smoke', async ({ page }, testInfo) => {
  const credentials = getCredentialsOrSkip(testInfo, 'E2E_CONTRACTOR');
  test.skip(!credentials, 'Missing contractor credentials');

  await loginViaKeycloak(page, credentials!);

  await gotoWithRetry(page, '/requests');
  await expect(page).toHaveURL(/\/requests/);

  const contractorLinks = page.locator('a[href*="/requests/"][href$="/contractor"]');
  if (await contractorLinks.count()) {
    await contractorLinks.first().click();
    await expect(page).toHaveURL(/\/requests\/\d+\/contractor/);
  }

  await logoutFromUi(page);
});

test('superadmin admin-page smoke @smoke', async ({ page }, testInfo) => {
  const credentials = getCredentialsOrSkip(testInfo, 'E2E_SUPERADMIN');
  test.skip(!credentials, 'Missing superadmin credentials');

  await loginViaKeycloak(page, credentials!);
  await gotoWithRetry(page, '/admin');
  await expect(page).toHaveURL(/\/admin/);
  await page.waitForLoadState('networkidle');

  await expect(page.locator('main')).toBeVisible();
  await logoutFromUi(page);
});
