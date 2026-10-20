import { writeFile } from 'node:fs/promises';
import { expect, test } from '@playwright/test';
import { assertNoSevereConsoleErrors, getCredentialsOrSkip, loginViaIam, logoutFromUi } from './helpers';

test('request -> offer -> workspace -> status update flow @request-offer', async ({ page }, testInfo) => {
  const economistCredentials = getCredentialsOrSkip(testInfo, 'E2E_ECONOMIST');
  const contractorCredentials = getCredentialsOrSkip(testInfo, 'E2E_CONTRACTOR');
  test.skip(!economistCredentials || !contractorCredentials, 'Economist and contractor credentials are required');

  await loginViaIam(page, economistCredentials!);

  await assertNoSevereConsoleErrors(page, async () => {
    await page.goto('/requests/create');
    await page.waitForLoadState('networkidle');
  });
  await expect(page.locator('body')).toContainText(/\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u0437\u0430\u044f\u0432\u043a\u0443/i);

  const uploadPath = testInfo.outputPath('request-offer-upload.txt');
  await writeFile(uploadPath, `request-offer flow ${Date.now()}`, 'utf8');
  await page.getByPlaceholder(/\u043a\u0440\u0430\u0442\u043a\u043e \u043e\u043f\u0438\u0448\u0438\u0442\u0435/i).fill('Auto e2e request-offer flow request');
  await page.getByPlaceholder(/\u0443\u043a\u0430\u0436\u0438\u0442\u0435 \u0441\u0443\u043c\u043c\u0443/i).fill('1000');
  await page.locator('input[type="file"]').first().setInputFiles(uploadPath);
  await page.getByRole('button', { name: /\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u0437\u0430\u044f\u0432\u043a\u0443/i }).click();
  await expect(page).toHaveURL(/\/requests/);

  await logoutFromUi(page);
  await loginViaIam(page, contractorCredentials!);

  await assertNoSevereConsoleErrors(page, async () => {
    await page.goto('/requests?tab=open');
    await page.waitForLoadState('networkidle');
  });
  const contractorRequestLinks = page.locator('a[href*="/requests/"][href$="/contractor"]');
  test.skip((await contractorRequestLinks.count()) === 0, 'No contractor-open request is available for offer creation');
  await contractorRequestLinks.first().click();
  await expect(page).toHaveURL(/\/requests\/\d+\/contractor/);

  const respondButton = page.getByRole('button', { name: /\u041e\u0442\u043a\u043b\u0438\u043a\u043d\u0443\u0442\u044c\u0441\u044f/i });
  if (await respondButton.isVisible()) {
    await page.getByPlaceholder(/\u0421\u0443\u043c\u043c\u0430 \u041a\u041f/i).fill('950');
    await respondButton.click();
    await page.waitForLoadState('networkidle');
  }

  await page.goto('/requests?tab=my');
  await page.waitForLoadState('networkidle');
  const workspaceLinks = page.locator('a[href*="/offers/"][href$="/workspace"]');
  test.skip((await workspaceLinks.count()) === 0, 'No contractor workspace link found after response');
  const workspacePath = await workspaceLinks.first().getAttribute('href');
  test.skip(!workspacePath, 'Workspace URL is empty');

  await logoutFromUi(page);
  await loginViaIam(page, economistCredentials!);
  await page.goto(workspacePath!);
  await expect(page).toHaveURL(/\/offers\/\d+\/workspace/);

  const statusSelect = page.locator('label:has-text("Статус"), [aria-label^="status-"]').first();
  await expect(statusSelect).toBeVisible();

  const selects = page.locator('div[role="combobox"]');
  if (await selects.count()) {
    await selects.first().click();
    const rejectedOption = page.getByRole('option', { name: /\u041e\u0442\u043a\u0430\u0437\u0430\u043d\u043e/i });
    if (await rejectedOption.count()) {
      await rejectedOption.first().click();
      await expect(page.locator('body')).toContainText(/\u041e\u0442\u043a\u0430\u0437\u0430\u043d\u043e|\u041f\u0440\u0438\u043d\u044f\u0442\u043e/i);
    }
  }

  await logoutFromUi(page);
});
