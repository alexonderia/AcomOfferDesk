import { readFileSync } from 'node:fs';
import { expect, test } from '@playwright/test';
import { loginViaIam } from './helpers';

test.use({ trace: 'off', video: 'off' });
const privatePath = process.env.E2E_QA_CREDENTIALS;
const enabled = process.env.E2E_EXPECT_EMAIL_ENABLED === 'true';

test('ready no-mail account survives enabling email and changes its own password @no-mail-transition', async ({ page, browser }) => {
  test.skip(!privatePath || !enabled, 'Requires dedicated QA credentials and a controlled mail-enabled backend');
  const values = JSON.parse(readFileSync(privatePath!, 'utf8')) as { ui_login: string; changed_password: string; users: { SUPERADMIN: { login: string; password: string } } };
  const capabilities = await page.request.get('/api/v1/auth/capabilities');
  expect((await capabilities.json()).data).toMatchObject({ email_enabled: true, direct_user_creation: false });
  await loginViaIam(page, { username: values.ui_login, password: values.changed_password });
  const session = await page.request.get('/api/v1/auth/session');
  expect((await session.json()).data).toMatchObject({ login: values.ui_login, status: 'active', email_enabled: true, business_access: true });
  const post = async (path: string, data: object, target = page) => {
    const csrf = (await target.context().cookies()).find((cookie) => cookie.name === 'acom_csrf')!.value;
    return target.request.post(`/api/v1${path}`, { data, headers: { 'X-CSRF-Token': csrf, Origin: new URL(target.url()).origin } });
  };
  const admin = await browser.newPage();
  await loginViaIam(admin, { username: values.users.SUPERADMIN.login, password: values.users.SUPERADMIN.password });
  const creation = await post('/users/register', { login: values.ui_login, role_id: 6, password: values.changed_password, password_confirmation: values.changed_password }, admin);
  expect(creation.status()).toBe(409);
  await admin.context().close();
  const temporary = `${values.changed_password}_transition`;
  expect((await post('/users/me/password', { current_password: values.changed_password, new_password: temporary, password_confirmation: temporary })).status()).toBe(204);
  await loginViaIam(page, { username: values.ui_login, password: temporary });
  expect((await post('/users/me/password', { current_password: temporary, new_password: values.changed_password, password_confirmation: values.changed_password })).status()).toBe(204);
});
