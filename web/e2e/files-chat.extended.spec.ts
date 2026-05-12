import { writeFile } from 'node:fs/promises';
import { expect, test } from '@playwright/test';
import { assertNoSevereConsoleErrors, getCredentialsOrSkip, loginViaKeycloak, logoutFromUi } from './helpers';

test('workspace files/chat flow and forbidden access check @files-chat', async ({ page }, testInfo) => {
  const contractorCredentials = getCredentialsOrSkip(testInfo, 'E2E_CONTRACTOR');
  const operatorCredentials = getCredentialsOrSkip(testInfo, 'E2E_OPERATOR');
  test.skip(!contractorCredentials || !operatorCredentials, 'Contractor and operator credentials are required');

  await loginViaKeycloak(page, contractorCredentials!);
  await page.goto('/requests?tab=my');
  await page.waitForLoadState('networkidle');

  const workspaceLinks = page.locator('a[href*="/offers/"][href$="/workspace"]');
  test.skip((await workspaceLinks.count()) === 0, 'No contractor workspace links available');
  const workspacePath = await workspaceLinks.first().getAttribute('href');
  test.skip(!workspacePath, 'Workspace URL is empty');

  await assertNoSevereConsoleErrors(page, async () => {
    await page.goto(workspacePath!);
    await page.waitForLoadState('networkidle');
  });
  await expect(page).toHaveURL(/\/offers\/\d+\/workspace/);

  const openChatButton = page.getByRole('button', { name: /\u041e\u0442\u043a\u0440\u044b\u0442\u044c \u0447\u0430\u0442/i });
  if (await openChatButton.isVisible().catch(() => false)) {
    await openChatButton.click();
  }

  const chatInput = page.getByPlaceholder(/\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435/i).first();
  if (await chatInput.count()) {
    const messageText = `e2e-files-chat-${Date.now()}`;
    await chatInput.fill(messageText);
    const sendButton = page.getByRole('button', { name: /\u041e\u0442\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435/i });
    await sendButton.click();
    await expect(page.locator('body')).toContainText(messageText);
  }

  const uploadPath = testInfo.outputPath('workspace-attachment.txt');
  await writeFile(uploadPath, `workspace attachment ${Date.now()}`, 'utf8');
  const fileInputs = page.locator('input[type="file"]');
  if (await fileInputs.count()) {
    await fileInputs.first().setInputFiles(uploadPath);
    await expect(page.locator('body')).toContainText(/workspace-attachment\.txt|attachment/i);
  }

  await logoutFromUi(page);

  await loginViaKeycloak(page, operatorCredentials!);
  await assertNoSevereConsoleErrors(page, async () => {
    await page.goto(workspacePath!);
    await page.waitForLoadState('networkidle');
  });
  expect(new URL(page.url()).pathname).not.toMatch(/\/offers\/\d+\/workspace/);
  await logoutFromUi(page);
});
