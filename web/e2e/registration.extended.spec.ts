import { expect, test } from '@playwright/test';
import { assertNoSevereConsoleErrors, getCredentialsOrSkip, loginViaKeycloak, logoutFromUi } from './helpers';

test('contractor invite registration happy path (manual if stand supports full flow) @registration', async ({ page }, testInfo) => {
  const inviteUrl = process.env.E2E_REGISTRATION_INVITE_URL?.trim() ?? '';
  test.skip(!inviteUrl, 'E2E_REGISTRATION_INVITE_URL is not set for invite-based registration flow');

  await assertNoSevereConsoleErrors(page, async () => {
    await page.goto(inviteUrl);
    await page.waitForLoadState('networkidle');
  });

  await expect(page.locator('body')).toContainText(/регистрац|invite|login|keycloak/i);

  const credentials = getCredentialsOrSkip(testInfo, 'E2E_CONTRACTOR');
  if (credentials) {
    await loginViaKeycloak(page, credentials);
    await expect(page).toHaveURL(/\/(requests|account|auth\/callback)/);
    await logoutFromUi(page);
  }
});
