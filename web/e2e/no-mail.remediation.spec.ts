import { readFileSync } from 'node:fs';
import { expect, test, type Page } from '@playwright/test';
import { createPdfFixture, loginViaIam } from './helpers';

type Account = { login: string; password: string; role_id: number };
type Credentials = { users: Record<string, Account>; ui_login: string; ui_password: string; changed_password: string };
const credentialsPath = process.env.E2E_QA_CREDENTIALS;
const credentials: Credentials | null = credentialsPath ? JSON.parse(readFileSync(credentialsPath, 'utf8')) : null;
test.use({ trace: 'off', video: 'off' });

const signIn = (page: Page, role: string) => {
  const account = credentials!.users[role];
  return loginViaIam(page, { username: account.login, password: account.password });
};
const api = async (page: Page, path: string, method = 'GET', data?: object) => {
  const token = (await page.context().cookies()).find((cookie) => cookie.name === 'acom_csrf')?.value ?? '';
  return page.request.fetch(`/api/v1${path}`, {
    method, data, headers: { 'X-CSRF-Token': token, Origin: new URL(page.url()).origin }
  });
};
const okData = async (response: Awaited<ReturnType<typeof api>>) => {
  expect(response.ok(), `HTTP ${response.status()}: ${(await response.text()).slice(0, 350)}`).toBeTruthy();
  return (await response.json()).data;
};

test.describe('No-mail remediation on a real stack @no-mail', () => {
  test.describe.configure({ mode: 'serial' });
  test.skip(!credentials, 'E2E_QA_CREDENTIALS must point to dedicated QA credentials');
  let rootA: number;
  let rootB: number;
  let teamA: number;
  let requestId: string;
  let offerId: number;

  test.beforeAll(async ({ browser }) => {
    const page = await browser.newPage();
    await signIn(page, 'SUPERADMIN');
    const roots = (await okData(await api(page, '/units/tree'))).items;
    const ensureUnit = async (name: string, parent?: number) => {
      const existing = roots.find((item: { name: string }) => item.name === name);
      return existing?.unit_id ?? (await okData(await api(page, '/units', 'POST', { name, id_parent: parent }))).unit_id;
    };
    rootA = await ensureUnit('QA v108 root A');
    rootB = await ensureUnit('QA v108 root B');
    const root = (await okData(await api(page, '/units/tree'))).items.find((item: { unit_id: number }) => item.unit_id === rootA);
    teamA = root.children.find((item: { name: string }) => item.name === 'QA v108 team A')?.unit_id
      ?? (await okData(await api(page, '/units', 'POST', { name: 'QA v108 team A', id_parent: rootA }))).unit_id;
    for (const [role, unit] of [['PROJECT_MANAGER', rootA], ['ADMIN', rootA], ['LEAD_ECONOMIST', teamA], ['ECONOMIST', teamA], ['OPERATOR', teamA]] as const) {
      const members = (await okData(await api(page, `/units/${unit}/members`))).items;
      if (!members.some((member: { user_id: string }) => member.user_id === credentials!.users[role].login)) {
        await okData(await api(page, `/units/${unit}/members`, 'POST', { user_id: credentials!.users[role].login }));
      }
    }
    await okData(await api(page, `/contractors/${credentials!.users.CONTRACTOR.login}/root-units`, 'PUT', { root_unit_ids: [rootA] }));
    await page.context().close();
  });

  test('UI creates a ready account without email; retries cannot change its password', async ({ page }) => {
    await signIn(page, 'SUPERADMIN');
    const capability = await okData(await api(page, '/auth/capabilities'));
    expect(capability.email_enabled).toBe(false);
    await page.goto('/admin?users_tab=economists&create=1');
    const dialog = page.getByRole('dialog');
    await expect(dialog.getByText('Почта отключена.', { exact: false })).toBeVisible();
    await dialog.locator('input[name="login"]').fill(credentials!.ui_login);
    await dialog.locator('input[name="password"]').fill(credentials!.ui_password);
    await dialog.locator('input[name="password_confirmation"]').fill(credentials!.ui_password);
    await dialog.getByRole('combobox', { name: 'Объединение' }).fill('QA v108 root B');
    await page.getByRole('option', { name: 'QA v108 root B', exact: true }).click();
    const created = page.waitForResponse((response) => response.url().endsWith('/api/v1/users/register') && response.request().method() === 'POST');
    await dialog.getByRole('button', { name: 'Создать сотрудника' }).click();
    expect((await created).status()).toBe(200);
    await expect(dialog.locator('input[name="login"]')).toHaveValue('');
    await dialog.press('Escape');
    await expect(dialog).not.toBeVisible();
    const payload = { login: credentials!.ui_login, role_id: 6, unit_id: rootB, password: credentials!.ui_password, password_confirmation: credentials!.ui_password };
    expect((await api(page, '/users/register', 'POST', payload)).status()).toBe(200);
    expect((await api(page, '/users/register', 'POST', { ...payload, password: 'Different password 123', password_confirmation: 'Different password 123' })).status()).toBe(409);
    expect((await api(page, '/users/register', 'POST', { ...payload, password_confirmation: 'Not matching password 123' })).status()).toBe(422);
    expect((await api(page, '/auth/password-reset/request', 'POST', { login: credentials!.ui_login })).status()).toBe(409);
  });

  test('profile changes password using the old one and requires a new login', async ({ page, browser }) => {
    await loginViaIam(page, { username: credentials!.ui_login, password: credentials!.ui_password });
    const profile = await okData(await api(page, '/users/me'));
    expect(profile.actions.can_manage_credentials).toBe(true);
    await page.getByRole('button', { name: 'Открыть профиль', exact: true }).click();
    const dialog = page.getByRole('dialog').filter({ has: page.getByRole('heading', { name: 'Изменение пароля' }) });
    await dialog.getByLabel(/^Текущий пароль\s*\*?$/).fill('Wrong current password 123');
    await dialog.getByLabel(/^Новый пароль\s*\*?$/).fill(credentials!.changed_password);
    await dialog.getByLabel(/^Повтор нового пароля\s*\*?$/).fill(credentials!.changed_password);
    const rejected = page.waitForResponse((response) => response.url().endsWith('/users/me/password'));
    await dialog.getByRole('button', { name: 'Сохранить пароль' }).click();
    expect((await rejected).status()).toBe(409);
    await expect(dialog.getByRole('alert')).toBeVisible();
    await dialog.getByLabel(/^Текущий пароль\s*\*?$/).fill(credentials!.ui_password);
    const changed = page.waitForResponse((response) => response.url().endsWith('/users/me/password'));
    await dialog.getByRole('button', { name: 'Сохранить пароль' }).click();
    expect((await changed).status()).toBe(204);
    await expect(page).toHaveURL(/login/);
    const reentry = await browser.newPage();
    await reentry.goto('/api/v1/auth/login?next=%2F');
    await reentry.locator('input[name="login"]').fill(credentials!.ui_login);
    await reentry.locator('input[name="password"]').fill(credentials!.ui_password);
    await reentry.locator('button[type="submit"]').click();
    await expect(reentry.locator('input[name="password"]')).toBeVisible();
    expect((await api(reentry, '/auth/session')).status()).toBe(401);
    await loginViaIam(reentry, { username: credentials!.ui_login, password: credentials!.changed_password });
    expect((await okData(await api(reentry, '/auth/session'))).login).toBe(credentials!.ui_login);
    await reentry.context().close();
  });

  test('real request/manual offer, chat hierarchy, feedback and delegated plan', async ({ page, browser }) => {
    test.setTimeout(180_000);
    await signIn(page, 'ECONOMIST');
    const files = (await okData(await api(page, '/normative-files?status=actual'))).items;
    expect(files.length).toBeGreaterThan(0);
    const token = (await page.context().cookies()).find((cookie) => cookie.name === 'acom_csrf')!.value;
    requestId = `QA-v108-${Date.now()}`;
    const request = await page.request.post('/api/v1/requests', {
      headers: { 'X-CSRF-Token': token, Origin: new URL(page.url()).origin },
      multipart: { id: requestId, description: 'QA v108 no-mail regression', deadline_at: new Date(Date.now() + 86400000).toISOString(), initial_amount: '1000', normative_file_id: String(files[0].id), files: { name: 'qa-v108.pdf', mimeType: 'application/pdf', buffer: createPdfFixture() } }
    });
    await okData(request);
    const eligible = await okData(await api(page, `/requests/${requestId}/offers/manual/eligible-contractors`));
    expect(eligible.items.some((item: { user_id: string }) => item.user_id === credentials!.users.CONTRACTOR.login)).toBe(true);
    const offer = await page.request.post(`/api/v1/requests/${requestId}/offers/manual`, { headers: { 'X-CSRF-Token': token, Origin: new URL(page.url()).origin }, multipart: { contractor_mode: 'existing', contractor_user_id: credentials!.users.CONTRACTOR.login, offer_amount: '900' } });
    offerId = (await okData(offer)).offer_id;
    const candidatesAfter = await okData(await api(page, `/requests/${requestId}/offers/manual/eligible-contractors`));
    expect(candidatesAfter.items.some((item: { user_id: string }) => item.user_id === credentials!.users.CONTRACTOR.login)).toBe(false);
    await okData(await api(page, `/offers/${offerId}/messages`, 'POST', { text: 'QA v108 first message without email' }));
    const feedback = await okData(await api(page, '/feedback', 'POST', { text: `QA v108 feedback ${requestId}` }));

    const lead = await browser.newPage();
    await signIn(lead, 'LEAD_ECONOMIST');
    const workspace = await okData(await api(lead, `/offers/${offerId}/workspace`));
    expect(workspace.chat_actions.can_send_message).toBe(true);
    await okData(await api(lead, `/offers/${offerId}/messages`, 'POST', { text: 'QA v108 lead reply' }));
    const pm = await browser.newPage();
    await signIn(pm, 'PROJECT_MANAGER');
    expect((await api(pm, `/offers/${offerId}/messages`, 'POST', { text: 'Should be denied' })).status()).toBe(403);
    const period = new Date().toISOString().slice(0, 7);
    expect((await api(page, '/plans/root', 'POST', { period, name: 'Forbidden economist root', plan_amount: 1000 })).status()).toBe(403);
    const dashboard = await okData(await api(pm, `/plans?period=${period}`));
    const rootPlan = dashboard.tree ?? dashboard.trees?.find((item: { user_id: string }) => item.user_id === credentials!.users.PROJECT_MANAGER.login)
      ?? await okData(await api(pm, '/plans/root', 'POST', { period, name: `QA v108 ${requestId}`, plan_amount: 10000 }));
    const delegated = rootPlan.children?.find((item: { user_id: string }) => item.user_id === credentials!.users.ECONOMIST.login)
      ?? await okData(await api(pm, '/plans/delegate', 'POST', { parent_plan_id: rootPlan.plan_id, child_user_id: credentials!.users.ECONOMIST.login, child_plan_amount: 3000 }));
    await okData(await api(page, `/requests/${requestId}`, 'PATCH', { id_plan: delegated.plan_id }));
    expect((await okData(await api(page, `/requests/${requestId}`))).item.id_plan).toBe(delegated.plan_id);
    await okData(await api(page, `/requests/${requestId}`, 'PATCH', { id_plan: null }));
    await lead.context().close();
    await pm.context().close();

    const sa = await browser.newPage();
    await signIn(sa, 'SUPERADMIN');
    const list = await okData(await api(sa, `/feedback?search=${encodeURIComponent(requestId)}`));
    const item = list.items.find((entry: { id: number }) => entry.id === feedback.feedback_id);
    expect(item.author_user_id).toBe(credentials!.users.ECONOMIST.login);
    expect(item.created_at).toBeTruthy();
    await sa.goto('/feedback');
    await expect(sa.getByText(`QA v108 feedback ${requestId}`, { exact: true })).toBeVisible();
    await sa.context().close();
  });

  test('exact INN, role reversal, blocking and department boundaries', async ({ page, browser }) => {
    await signIn(page, 'SUPERADMIN');
    const inn = (base: string) => base + String([2, 4, 10, 3, 5, 9, 4, 6, 8].reduce((sum, weight, index) => sum + weight * Number(base[index]), 0) % 11 % 10);
    const base = String(Date.now()).slice(-8);
    const firstInn = inn('9' + base);
    const secondInn = inn('8' + base);
    const company = { company_name: 'QA v108 identical company name', company_phone: '+79991234567' };
    const first = await okData(await api(page, '/users/manual-contractor', 'POST', { ...company, inn: firstInn }));
    const second = await okData(await api(page, '/users/manual-contractor', 'POST', { ...company, inn: secondInn }));
    expect(first.user_id).not.toBe(second.user_id);
    const reused = await okData(await api(page, '/users/manual-contractor', 'POST', { ...company, company_name: 'QA v108 submitted different name', inn: firstInn }));
    expect(reused.user_id).toBe(first.user_id);
    await okData(await api(page, `/users/${credentials!.ui_login}/role`, 'PATCH', { role_id: 3 }));
    await okData(await api(page, `/users/${credentials!.ui_login}/role`, 'PATCH', { role_id: 6 }));
    const admin = await browser.newPage();
    await signIn(admin, 'ADMIN');
    expect((await api(admin, `/users/${credentials!.ui_login}/status`, 'PATCH', { user_status: 'inactive' })).status()).toBe(403);
    await admin.context().close();
    await okData(await api(page, `/users/${credentials!.ui_login}/status`, 'PATCH', { user_status: 'inactive' }));
    const blocked = await browser.newPage();
    await blocked.goto('/api/v1/auth/login?next=%2F');
    await blocked.locator('input[name="login"]').fill(credentials!.ui_login);
    await blocked.locator('input[name="password"]').fill(credentials!.changed_password);
    await blocked.locator('button[type="submit"]').click();
    await expect(blocked.locator('input[name="password"]')).toBeVisible();
    expect((await api(blocked, '/auth/session')).status()).toBe(401);
    await okData(await api(page, `/users/${credentials!.ui_login}/status`, 'PATCH', { user_status: 'active' }));
    await loginViaIam(blocked, { username: credentials!.ui_login, password: credentials!.changed_password });
    expect((await okData(await api(blocked, '/auth/session'))).role_id).toBe(6);
    await blocked.context().close();
  });
});
