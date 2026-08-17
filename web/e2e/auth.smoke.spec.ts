import { expect, test } from '@playwright/test';
import { getCredentialsOrSkip, gotoWithRetry, loginViaIam, logoutFromUi } from './helpers';

test('login smoke @smoke', async ({ page }, testInfo) => {
  const credentials = getCredentialsOrSkip(testInfo, 'E2E_SUPERADMIN');
  test.skip(!credentials, 'Missing superadmin credentials');

  await loginViaIam(page, credentials!);
  await gotoWithRetry(page, '/requests');
  await expect(page).toHaveURL(/\/requests|\/pm-dashboard|\/admin|\/account/);

  await logoutFromUi(page);
});
