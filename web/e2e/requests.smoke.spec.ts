import { expect, test } from '@playwright/test';
import { getCredentialsOrSkip, loginViaKeycloak, logoutFromUi } from './helpers';

const assertNoSevereConsoleErrors = async (page, action: () => Promise<void>) => {
  const severeErrors: string[] = [];
  const listener = (msg) => {
    if (msg.type() === 'error') {
      const text = msg.text();
      if (text.includes('the server responded with a status of 401')) {
        return;
      }
      severeErrors.push(text);
    }
  };

  page.on('console', listener);
  try {
    await action();
  } finally {
    page.off('console', listener);
  }

  expect(severeErrors, `Console errors: ${severeErrors.join('\n')}`).toEqual([]);
};

test('economist requests smoke @smoke', async ({ page }, testInfo) => {
  const credentials = getCredentialsOrSkip(testInfo, 'E2E_ECONOMIST');
  test.skip(!credentials, 'Missing economist credentials');

  await loginViaKeycloak(page, credentials!);

  await assertNoSevereConsoleErrors(page, async () => {
    await page.goto('/requests');
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

  await page.goto('/requests');
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
  await page.goto('/admin');
  await expect(page).toHaveURL(/\/admin/);
  await page.waitForLoadState('networkidle');

  await expect(page.locator('main')).toBeVisible();
  await logoutFromUi(page);
});
