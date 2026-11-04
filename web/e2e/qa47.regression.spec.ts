import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { expect, test } from '@playwright/test';
import { loginViaIam, logoutFromUi } from './helpers';
import { dataset, datasetPath, encoded, pdf, QA47 } from './qa47/support';

test.use({ trace: 'off', video: 'off' });
test.skip(!dataset, 'Requires an isolated QA47 dataset via E2E_QA47_CREDENTIALS');
let qa: QA47;
const five = ['SUPERADMIN', 'ADMIN', 'ECONOMIST', 'LEAD_ECONOMIST', 'PROJECT_MANAGER'];
const ownPath = () => '/requests/' + encoded(qa.state.requests.A1.id);

test.beforeAll(async ({ browser }) => {
  test.setTimeout(180000);
  qa = new QA47(browser, dataset!);
  await qa.setup();
});
test.afterAll(async () => { await qa?.close(); });
test.afterEach(async ({}, info) => {
  const number = Number(info.title.match(/QA47-(\d+)/)?.[1]);
  const result = { number, title: info.title, status: info.status ?? 'unknown', duration: info.duration };
  qa.results.push(result);
  const path = join(dirname(datasetPath!), 'qa47-results.json');
  let previous: typeof qa.results = [];
  try {
    const saved = JSON.parse(readFileSync(path, 'utf8'));
    if (saved.batch === qa.data.batch) previous = saved.results;
  } catch { /* First recorded attempt of this dataset. */ }
  writeFileSync(path, JSON.stringify({ batch: qa.data.batch, results: [...previous, result] }, null, 2));
});

test('QA47-01 ready identities, refresh, second tab and login without unit', async ({ browser }) => {
  for (const role of [...five, 'SPARE']) {
    const page = await qa.page(role);
    const session = await qa.ok(role, '/auth/session');
    expect(session).toMatchObject({ login: qa.user(role).login, role_id: qa.user(role).role_id, business_access: true });
    await page.reload();
    const tab = await page.context().newPage();
    await tab.goto(role === 'ADMIN' ? '/admin' : '/pm-dashboard');
    await expect(tab.locator('main')).toBeVisible();
    expect((await tab.request.get('/api/v1/auth/session')).status()).toBe(200);
    await tab.close();
  }
  const anonymous = await browser.newContext({ baseURL: 'http://localhost:8080' });
  const page = await anonymous.newPage();
  await page.goto('/api/v1/auth/login');
  await page.locator('button[type="submit"]').click();
  expect(await page.locator('input[name="login"]').evaluate((input: HTMLInputElement) => input.validity.valueMissing)).toBe(true);
  await page.locator('input[name="login"]').fill(qa.data.batch + '_missing');
  await page.locator('input[name="password"]').fill('Invalid test password');
  await page.locator('button[type="submit"]').click();
  expect((await page.request.get('/api/v1/auth/session')).status()).toBe(401);
  await anonymous.close();
});

test('QA47-02 logout, back navigation, direct URL and re-entry', async () => {
  for (const role of five) {
    const page = await qa.page(role);
    await logoutFromUi(page);
    await expect(page.getByRole('heading', { name: 'Вход в AcomOfferDesk' })).toBeVisible();
    expect((await page.request.get('/api/v1/auth/session')).status()).toBe(401);
    await page.goBack();
    await expect(page.getByRole('heading', { name: 'Вход в AcomOfferDesk' })).toBeVisible();
    await page.reload();
    expect((await page.request.get('/api/v1/auth/session')).status()).toBe(401);
    await loginViaIam(page, { username: qa.user(role).login, password: qa.user(role).password });
    expect((await qa.ok(role, '/auth/session')).login).toBe(qa.user(role).login);
  }
});

test('QA47-03 invalid public links and completed-account routing', async ({ browser }) => {
  const context = await browser.newContext({ baseURL: 'http://localhost:8080' });
  for (const path of ['/auth/login', '/register', '/verify-email?token=invalid', '/auth/registration-link-status', '/login?reset=1']) {
    const page = await context.newPage();
    await page.goto(path);
    await expect(page.locator('body')).not.toBeEmpty();
    expect((await page.request.get('/api/v1/auth/session')).status()).toBe(401);
    await page.close();
  }
  expect([302, 303, 400, 401, 422]).toContain((await context.request.get('/api/v1/auth/callback', { maxRedirects: 0 })).status());
  await context.close();
  const ready = await qa.page('ECONOMIST');
  for (const path of ['/account', '/profile/onboarding', '/', '/qa47-nonexistent-route']) {
    await ready.goto(path);
    await expect(ready.locator('main')).toBeVisible();
    expect((await qa.ok('ECONOMIST', '/auth/session')).business_access).toBe(true);
  }
});

test('QA47-04 full five-role route matrix and contractor-view boundaries', async () => {
  test.setTimeout(180000);
  const paths = ['/requests', '/requests/create', ownPath(), `/offers/${qa.state.requests.A1.offers[0]}/workspace`, '/admin', '/admin/hierarchy', '/contractors', '/normative-files', '/pm-dashboard', '/pm-dashboard/savings', '/pm-dashboard/plan', '/feedback'];
  for (const role of five) {
    const page = await qa.page(role);
    for (const path of paths) {
      const allowed = role === 'ADMIN' ? ['/admin', '/admin/hierarchy'].includes(path)
        : path === '/feedback' ? role === 'SUPERADMIN'
          : path === '/normative-files' ? ['SUPERADMIN', 'LEAD_ECONOMIST'].includes(role)
            : path === '/requests/create' ? role !== 'PROJECT_MANAGER' : true;
      await page.goto(path);
      await page.waitForLoadState('networkidle');
      if (allowed) { expect(new URL(page.url()).pathname).toBe(path); await expect(page.locator('main')).toBeVisible(); }
      else expect(new URL(page.url()).pathname).not.toBe(path);
    }
  }
  await qa.denied('ECONOMIST', ownPath() + '/offers', 'POST', { offer_amount: 500 });
  await qa.denied('ECONOMIST', '/requests/' + encoded(qa.state.requests.B.id) + '/contractor-view');
});

test('QA47-05 shared dialogs, keyboard focus, mobile viewport and create cancellation', async () => {
  const page = await qa.page('ECONOMIST');
  await page.goto('/requests');
  for (const name of ['Открыть профиль', 'Открыть форму обратной связи', 'Открыть памятку по роли']) {
    await page.getByRole('button', { name, exact: true }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await page.keyboard.press('Tab');
    expect(await page.evaluate(() => document.activeElement?.tagName)).not.toBe('BODY');
    await page.keyboard.press('Escape');
  }
  await page.getByRole('button', { name: 'Уведомления', exact: true }).click();
  await page.keyboard.press('Escape');
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator('main')).toBeVisible();
  await page.setViewportSize({ width: 1440, height: 1000 });
  const before = (await qa.ok('ECONOMIST', '/requests')).items.length;
  await page.goto('/requests/create');
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.keyboard.press('Escape');
  expect((await qa.ok('ECONOMIST', '/requests')).items.length).toBe(before);
});

test('QA47-06 request loading recovers after network failure', async () => {
  const page = await qa.page('ECONOMIST');
  const requestsUrl = /\/api\/v1\/requests(?:\?.*)?$/;
  await page.route(requestsUrl, (route) => route.abort('failed'));
  await page.goto('/requests');
  await expect(page.getByText(/загруз|соединени|сети/i).first()).toBeVisible();
  await page.unroute(requestsUrl);
  await page.reload();
  await expect(page.locator('main')).toBeVisible();
  await qa.ok('ECONOMIST', ownPath(), 'PATCH', { deadline_at: new Date(Date.now() + 86400000 * 4).toISOString() });
});

test('QA47-07 staff search, paging, profile scope and no editing by inspection', async () => {
  const page = await qa.page('ADMIN');
  await page.goto('/admin?users_tab=economists');
  await page.getByPlaceholder('Найти сотрудника').fill(qa.user('ECONOMIST').login);
  await expect(page.getByText(qa.name('ECONOMIST'), { exact: true })).toBeVisible();
  await expect(page.getByText(qa.name('FOREIGN'), { exact: true })).toHaveCount(0);
  await page.getByPlaceholder('Найти сотрудника').clear();
  const list = await qa.ok('ADMIN', '/users');
  expect(list.items.some((item: { user_id: string }) => item.user_id === qa.user('ECONOMIST').login)).toBe(true);
  await qa.ok('PROJECT_MANAGER', `/users/${qa.user('ECONOMIST').login}/profile`);
  await qa.ok('ECONOMIST', `/users/${qa.user('SUBORDINATE').login}/profile`);
  await qa.denied('ADMIN', `/users/${qa.user('FOREIGN').login}/hierarchy`);
  await qa.denied('ECONOMIST', `/users/${qa.user('FOREIGN').login}/profile`);
  const hierarchy = await qa.ok('SUPERADMIN', `/users/${qa.user('ECONOMIST').login}/hierarchy`);
  expect(hierarchy.units.length).toBeGreaterThan(0);
});

test('QA47-08 allowed employee creation and validation/role boundaries', async () => {
  const page = await qa.page('SUPERADMIN');
  await page.goto('/admin?users_tab=economists&create=1');
  const dialog = page.getByRole('dialog');
  await dialog.locator('input[name="login"]').fill(qa.data.batch + '_invalid_ui');
  await dialog.locator('input[name="password"]').fill(qa.user('SPARE').password);
  await dialog.locator('input[name="password_confirmation"]').fill(qa.user('SPARE').password);
  await dialog.locator('input[name="phone"]').fill('+7123');
  await dialog.getByRole('button', { name: 'Создать сотрудника' }).click();
  await expect(dialog.locator('input[name="phone"]')).toHaveAttribute('aria-invalid', 'true');
  await dialog.press('Escape');
  for (const role of ['SUPERADMIN', 'ADMIN', 'LEAD_ECONOMIST']) {
    const payload = { login: qa.data.batch + '_created_' + role.toLowerCase() + '_' + Date.now(), role_id: 6, full_name: 'QA47 created ' + role, password: qa.user('SPARE').password, password_confirmation: qa.user('SPARE').password, unit_id: qa.unit('A1') };
    await qa.invalid(role, '/users/register', 'POST', { ...payload, mail: 'invalid' });
    await qa.ok(role, '/users/register', 'POST', payload);
    await qa.invalid(role, '/users/register', 'POST', { ...payload, password: 'Different password 123', password_confirmation: 'Different password 123' });
  }
  for (const role of ['ECONOMIST', 'PROJECT_MANAGER']) await qa.denied(role, '/users/register', 'POST', { login: qa.data.batch + '_denied', role_id: 6, password: qa.user('SPARE').password, password_confirmation: qa.user('SPARE').password });
  await qa.denied('ADMIN', '/users/register', 'POST', { login: qa.data.batch + '_bad_role', role_id: 1, password: qa.user('SPARE').password, password_confirmation: qa.user('SPARE').password });
});

test('QA47-09 role conversion and forbidden promotion/scope', async () => {
  const path = `/users/${qa.user('SPARE').login}/role`;
  await qa.ok('SUPERADMIN', path, 'PATCH', { role_id: 3 });
  await qa.ok('SUPERADMIN', path, 'PATCH', { role_id: 6 });
  await qa.denied('ECONOMIST', path, 'PATCH', { role_id: 5 });
  await qa.denied('ADMIN', path, 'PATCH', { role_id: 1 });
  await qa.denied('PROJECT_MANAGER', `/users/${qa.user('FOREIGN').login}/role`, 'PATCH', { role_id: 5 });
});

test('QA47-10 blocking/recovery preserves credentials and respects scope', async () => {
  const target = qa.user('SPARE').login;
  await qa.ok('SUPERADMIN', `/users/${target}/status`, 'PATCH', { user_status: 'active' });
  await qa.pages.get('SPARE')?.context().close(); qa.pages.delete('SPARE');
  await qa.page('SPARE');
  expect((await qa.ok('SPARE', '/auth/session')).login).toBe(target);
  await qa.ok('SUPERADMIN', `/users/${target}/status`, 'PATCH', { user_status: 'inactive' });
  expect((await qa.api('SPARE', '/auth/session', 'GET', undefined, false)).status()).toBe(401);
  await qa.ok('SUPERADMIN', `/users/${target}/status`, 'PATCH', { user_status: 'active' });
  await (await qa.page('SPARE')).context().close(); qa.pages.delete('SPARE');
  expect((await qa.ok('SPARE', '/auth/session')).login).toBe(target);
  await qa.denied('ECONOMIST', `/users/${qa.user('FOREIGN').login}/status`, 'PATCH', { user_status: 'inactive' });
});

test('QA47-11 prepared review approval requires verified email without delivery', async () => {
  await qa.ok('ADMIN', `/contractors/${qa.user('REVIEW_VERIFIED').login}/status`, 'PATCH', { user_status: 'active' });
  await qa.invalid('ADMIN', `/contractors/${qa.user('REVIEW_UNVERIFIED').login}/status`, 'PATCH', { user_status: 'active' });
  await qa.ok('SUPERADMIN', `/contractors/${qa.user('REVIEW_UNVERIFIED').login}/status`, 'PATCH', { user_status: 'inactive' });
});

test('QA47-12 multiple memberships, transfer, unassigned login and restored scope', async () => {
  const target = qa.user('SPARE').login;
  const add = (unit: string) => qa.ok('SUPERADMIN', `/units/${qa.unit(unit)}/members`, 'POST', { user_id: target });
  const remove = (unit: string) => qa.ok('SUPERADMIN', `/units/${qa.unit(unit)}/members/${target}`, 'DELETE');
  await add('A1'); await add('A2'); await remove('A1');
  await qa.ok('SPARE', '/requests/' + encoded(qa.state.requests.A2.id));
  await qa.denied('SPARE', ownPath());
  await remove('A2');
  expect((await qa.ok('SPARE', '/auth/session')).business_access).toBe(true);
  await qa.denied('SPARE', '/requests/' + encoded(qa.state.requests.A2.id));
  await add('A1');
});

test('QA47-13 unit create/rename, invalid names and management boundaries', async () => {
  const unit = await qa.ok('SUPERADMIN', '/units', 'POST', { name: qa.data.batch + '_temporary', id_parent: qa.unit('A1') });
  await qa.ok('SUPERADMIN', `/units/${unit.unit_id}`, 'PATCH', { name: qa.data.batch + '_renamed' });
  await qa.invalid('SUPERADMIN', '/units', 'POST', { name: '', id_parent: qa.unit('A1') });
  await qa.denied('ADMIN', `/units/${qa.unit('B')}`, 'PATCH', { name: 'forbidden' });
  await qa.denied('ADMIN', `/units/${qa.unit('A')}/members/${qa.user('SUPERADMIN').login}`, 'DELETE');
  await qa.ok('SUPERADMIN', `/units/${unit.unit_id}`, 'DELETE');
});

test('QA47-14 unit moves reject cycles and cross-root transfer, deletion preserves members', async () => {
  const parent = await qa.ok('SUPERADMIN', '/units', 'POST', { name: qa.data.batch + '_parent', id_parent: qa.unit('A') });
  const child = await qa.ok('SUPERADMIN', '/units', 'POST', { name: qa.data.batch + '_child', id_parent: parent.unit_id });
  await qa.invalid('SUPERADMIN', `/units/${parent.unit_id}`, 'PATCH', { id_parent: child.unit_id });
  await qa.invalid('SUPERADMIN', `/units/${child.unit_id}`, 'PATCH', { id_parent: qa.unit('B') });
  await qa.ok('SUPERADMIN', `/units/${child.unit_id}`, 'PATCH', { id_parent: qa.unit('A2') });
  await qa.ok('SUPERADMIN', `/units/${parent.unit_id}`, 'DELETE');
  await qa.ok('SUPERADMIN', `/units/${child.unit_id}`, 'DELETE');
  await qa.invalid('SUPERADMIN', `/units/${qa.unit('A')}`, 'DELETE', {});
});

test('QA47-15 manual contractor creation validation and optional email', async () => {
  const payload = { company_name: 'QA47 manual ' + qa.data.batch, inn: qa.user('SPARE').inn, company_phone: '+79991234567' };
  await qa.invalid('ECONOMIST', '/users/manual-contractor', 'POST', { ...payload, inn: '123' });
  await qa.invalid('ECONOMIST', '/users/manual-contractor', 'POST', { ...payload, company_phone: 'invalid' });
  const created = await qa.ok('ECONOMIST', '/users/manual-contractor', 'POST', payload);
  const roots = await qa.ok('SUPERADMIN', `/contractors/${created.user_id}/root-units`);
  expect(JSON.stringify(roots)).toContain(String(qa.unit('A')));
  const list = await qa.ok('ECONOMIST', `/contractors?search=${encoded(payload.inn)}&limit=1&offset=0`);
  expect(list.items.some((item: { user_id: string }) => item.user_id === created.user_id)).toBe(true);
});

test('QA47-16 exact company reuse keeps the canonical record', async () => {
  const result = await qa.ok('ECONOMIST', '/users/manual-contractor', 'POST', { company_name: 'QA47 attempted replacement', inn: qa.user('CONTRACTOR').inn, company_phone: '+79990000000' });
  expect(result.user_id).toBe(qa.user('CONTRACTOR').login);
  const actual = await qa.ok('SUPERADMIN', `/contractors/${result.user_id}`);
  expect(JSON.stringify(actual)).toContain('QA47 CONTRACTOR');
  expect(JSON.stringify(actual)).not.toContain('attempted replacement');
});

test('QA47-17 manual contractor contact changes persist and validate', async () => {
  const path = `/users/${qa.user('CONTRACTOR').login}/manual-contractor`;
  await qa.invalid('ECONOMIST', path, 'PATCH', { company_phone: 'invalid' });
  await qa.ok('ECONOMIST', path, 'PATCH', { address: 'QA47 updated address', note: 'QA47 note' });
  const actual = await qa.ok('SUPERADMIN', `/contractors/${qa.user('CONTRACTOR').login}`);
  expect(JSON.stringify(actual)).toContain('QA47 updated address');
  await qa.invalid('ECONOMIST', `/users/${qa.user('ORDINARY').login}/manual-contractor`, 'PATCH', { address: 'forbidden ordinary edit' });
  expect(JSON.stringify(await qa.ok('SUPERADMIN', `/contractors/${qa.user('ORDINARY').login}`))).not.toContain('forbidden ordinary edit');
});

test('QA47-18 contractor status/root bindings require dedicated authority', async () => {
  const id = qa.user('HIDDEN').login;
  for (const role of ['ECONOMIST', 'LEAD_ECONOMIST', 'PROJECT_MANAGER']) await qa.denied(role, `/contractors/${id}/status`, 'PATCH', { user_status: 'inactive' });
  await qa.ok('ADMIN', `/contractors/${id}/status`, 'PATCH', { user_status: 'inactive' });
  await qa.ok('ADMIN', `/contractors/${id}/status`, 'PATCH', { user_status: 'active' });
  await qa.ok('SUPERADMIN', `/contractors/${id}/root-units`, 'PUT', { root_unit_ids: [qa.unit('A'), qa.unit('B')] });
  await qa.ok('SUPERADMIN', `/contractors/${id}/root-units`, 'PUT', { root_unit_ids: [qa.unit('A')] });
  await qa.invalid('SUPERADMIN', `/units/${qa.unit('A1')}/members`, 'POST', { user_id: id });
});

test('QA47-19 normative create/replace/status and read-only boundaries', async () => {
  const tag = Date.now();
  const makeFile = (name: string) => ({ name: qa.data.batch + '-' + tag + '-' + name + '.pdf', mimeType: 'application/pdf', buffer: pdf(qa.data.batch + tag + name) });
  const created = await qa.unwrap(await qa.multipart('LEAD_ECONOMIST', '/normative-files', { file: makeFile('normative') }));
  const id = created.normative_id;
  expect((await qa.multipart('LEAD_ECONOMIST', '/normative-files', { file: makeFile('normative') })).status()).toBe(409);
  const previous = qa.state.normative;
  let copy;
  try { qa.state.normative = id; copy = await qa.request('19_copy_' + tag); }
  finally { qa.state.normative = previous; qa.save(); }
  const replaced = await qa.unwrap(await qa.multipart('LEAD_ECONOMIST', `/normative-files/${id}`, { file: makeFile('replacement') }));
  expect(replaced.file_id).not.toBe(created.file_id);
  const same = await qa.unwrap(await qa.multipart('LEAD_ECONOMIST', `/normative-files/${id}`, { file: makeFile('replacement') }));
  expect(same.file_id).toBe(replaced.file_id);
  await qa.ok('LEAD_ECONOMIST', `/normative-files/${id}/status`, 'PATCH', { status: 'outdated' });
  expect((await qa.ok('ECONOMIST', '/normative-files?status=actual')).items.some((item: { id: number }) => item.id === id)).toBe(false);
  const oldFiles = (await qa.ok('ECONOMIST', '/requests/' + encoded(copy!.id))).item.files;
  const old = oldFiles.find((file: { name: string }) => file.name === makeFile('normative').name);
  expect(old).toBeTruthy();
  expect((await (await qa.api('ECONOMIST', `/files/${old.id}/download`)).body()).equals(makeFile('normative').buffer)).toBe(true);
  for (const role of ['ADMIN', 'ECONOMIST', 'PROJECT_MANAGER']) {
    await qa.denied(role, `/normative-files/${id}/status`, 'PATCH', { status: 'actual' });
    expect((await qa.api(role, `/files/${replaced.file_id}/download`)).ok()).toBe(true);
    expect((await qa.multipart(role, `/normative-files/${id}`, { file: makeFile('unauthorized') })).status()).toBe(403);
  }
  await qa.ok('LEAD_ECONOMIST', `/normative-files/${id}/status`, 'PATCH', { status: 'actual' });
});

test('QA47-20 request lists and direct access follow A1/A2/B hierarchy', async () => {
  const own = qa.state.requests.A1.id, child = qa.state.requests.A11.id, peer = qa.state.requests.A2.id, foreign = qa.state.requests.B.id;
  for (const role of ['ECONOMIST', 'LEAD_ECONOMIST', 'PROJECT_MANAGER', 'SUPERADMIN']) {
    const ids = (await qa.ok(role, '/requests')).items.map((item: { request_id: string }) => item.request_id);
    expect(ids).toContain(own);
    expect(ids).toContain(child);
    if (['PROJECT_MANAGER', 'SUPERADMIN'].includes(role)) expect(ids).toContain(peer);
    else expect(ids).not.toContain(peer);
    if (role === 'SUPERADMIN') expect(ids).toContain(foreign); else expect(ids).not.toContain(foreign);
  }
  await qa.denied('ECONOMIST', '/requests/' + encoded(foreign));
});

test('QA47-21 required fields, unique number and encoded request link', async () => {
  const fields = { id: qa.data.batch + '_21invalid', initial_amount: '-1', deadline_at: new Date(Date.now() + 86400000).toISOString(), normative_file_id: String(qa.state.normative), files: { name: 'qa47.pdf', mimeType: 'application/pdf', buffer: pdf('QA47 invalid') } };
  expect([409, 422]).toContain((await qa.multipart('ECONOMIST', '/requests', fields)).status());
  expect([409, 422]).toContain((await qa.multipart('ECONOMIST', '/requests', { ...fields, id: qa.state.requests.A1.id, initial_amount: '1000' })).status());
  const created = await qa.request('21 special + (A)');
  const page = await qa.page('ECONOMIST');
  await page.goto('/requests/' + encoded(created.id));
  await expect(page.getByRole('heading', { name: 'Заявка №' + created.id, exact: true })).toBeVisible();
});

test('QA47-22 hidden, inactive and foreign contractors stay outside eligibility', async () => {
  const hidden = await qa.request('22_hidden', 'ECONOMIST', [qa.user('HIDDEN').login]);
  const control = await qa.request('22_control');
  const eligible = (await qa.ok('ECONOMIST', `/requests/${encoded(hidden.id)}/offers/manual/eligible-contractors`)).items.map((item: { user_id: string }) => item.user_id);
  expect(eligible).toContain(qa.user('CONTRACTOR').login);
  for (const role of ['HIDDEN', 'INACTIVE', 'FOREIGN_CONTRACTOR']) expect(eligible).not.toContain(qa.user(role).login);
  await qa.denied('HIDDEN', `/requests/${encoded(hidden.id)}/contractor-view`);
  await qa.ok('HIDDEN', `/requests/${encoded(control.id)}/contractor-view`);
});

test('QA47-23 request edits and file validation/download/deletion', async () => {
  const request = await qa.request('23_files');
  const path = '/requests/' + encoded(request.id);
  await qa.invalid('ECONOMIST', path, 'PATCH', { initial_amount: -1 });
  await qa.ok('ECONOMIST', path, 'PATCH', { initial_amount: 120000, deadline_at: new Date(Date.now() + 86400000 * 5).toISOString() });
  const downloaded = await qa.api('ECONOMIST', `/files/${request.file}/download`);
  expect(downloaded.ok()).toBe(true); expect((await downloaded.body()).subarray(0, 4).toString()).toBe('%PDF');
  for (const file of [{ name: 'empty.pdf', mimeType: 'application/pdf', buffer: Buffer.alloc(0) }, { name: 'bad.exe', mimeType: 'application/octet-stream', buffer: Buffer.from('MZ invalid QA47') }, { name: 'large.pdf', mimeType: 'application/pdf', buffer: Buffer.alloc(6 * 1024 * 1024) }]) {
    expect([413, 422]).toContain((await qa.multipart('ECONOMIST', path + '/files', { file })).status());
  }
  const added = await qa.unwrap(await qa.multipart('ECONOMIST', path + '/files', { file: { name: 'extra.pdf', mimeType: 'application/pdf', buffer: pdf(request.id + 'extra') } }));
  await qa.ok('ECONOMIST', path + `/files/${added.file_id}`, 'DELETE');
  const files = (await qa.ok('ECONOMIST', path)).item.files;
  expect(files.some((file: { id: number }) => file.id === request.file)).toBe(true);
  expect(files.some((file: { id: number }) => file.id === added.file_id)).toBe(false);
});

test('QA47-24 project manager reads procurement but cannot perform base mutations', async () => {
  await qa.ok('PROJECT_MANAGER', ownPath());
  const offer = qa.state.requests.A1.offers[0];
  await qa.ok('PROJECT_MANAGER', `/offers/${offer}/workspace`);
  expect((await qa.api('PROJECT_MANAGER', `/files/${qa.state.requests.A1.file}/download`)).ok()).toBe(true);
  await qa.denied('PROJECT_MANAGER', ownPath(), 'PATCH', { initial_amount: 200000 });
  await qa.denied('PROJECT_MANAGER', `/offers/${offer}`, 'PATCH', { offer_amount: 79000 });
  await qa.denied('PROJECT_MANAGER', `/offers/${offer}/status`, 'PATCH', { status: 'accepted' });
  await qa.denied('PROJECT_MANAGER', `/offers/${offer}/messages`, 'POST', { text: 'QA47 forbidden' });
  await qa.denied('ADMIN', ownPath());
  await qa.denied('ADMIN', `/offers/${offer}/workspace`);
  await qa.denied('ECONOMIST', ownPath(), 'PATCH', { owner_user_id: qa.user('SUBORDINATE').login });
});

test('QA47-25 owner reassignment uses eligible users and preserves data', async () => {
  const request = await qa.request('25_owner');
  const path = '/requests/' + encoded(request.id);
  const candidates = (await qa.ok('PROJECT_MANAGER', path + '/eligible-owners')).items.map((item: { user_id: string }) => item.user_id);
  expect(candidates).toContain(qa.user('SUBORDINATE').login);
  expect(candidates).not.toContain(qa.user('FOREIGN').login);
  await qa.ok('PROJECT_MANAGER', path, 'PATCH', { owner_user_id: qa.user('SUBORDINATE').login });
  expect((await qa.ok('SUPERADMIN', path)).item.owner_user_id).toBe(qa.user('SUBORDINATE').login);
  await qa.denied('PROJECT_MANAGER', path, 'PATCH', { owner_user_id: qa.user('FOREIGN').login });
  await qa.ok('PROJECT_MANAGER', path, 'PATCH', { owner_user_id: qa.user('ECONOMIST').login });
});

test('QA47-26 own delegated plan links, foreign plan is rejected, unlink persists', async () => {
  const plans = await qa.plans();
  await qa.ok('ECONOMIST', ownPath(), 'PATCH', { id_plan: plans.own });
  expect((await qa.ok('ECONOMIST', ownPath())).item.id_plan).toBe(plans.own);
  expect([403, 404, 409]).toContain((await qa.api('ECONOMIST', ownPath(), 'PATCH', { id_plan: plans.foreign })).status());
  expect((await qa.ok('ECONOMIST', ownPath())).item.id_plan).toBe(plans.own);
  await qa.ok('ECONOMIST', ownPath(), 'PATCH', { id_plan: null });
  expect((await qa.ok('ECONOMIST', ownPath())).item.id_plan).toBeNull();
});

test('QA47-27 manual offer rejects duplicates and prohibited suppliers; new company works', async () => {
  const request = await qa.request('27_manual');
  await qa.offer(request);
  const existing = { contractor_mode: 'existing', contractor_user_id: qa.user('CONTRACTOR').login, offer_amount: '80000' };
  expect((await qa.multipart('ECONOMIST', `/requests/${encoded(request.id)}/offers/manual`, existing)).status()).toBe(409);
  for (const role of ['INACTIVE', 'FOREIGN_CONTRACTOR']) expect([403, 409]).toContain((await qa.multipart('ECONOMIST', `/requests/${encoded(request.id)}/offers/manual`, { ...existing, contractor_user_id: qa.user(role).login })).status());
  const created = await qa.unwrap(await qa.multipart('ECONOMIST', `/requests/${encoded(request.id)}/offers/manual`, { contractor_mode: 'new', company_name: 'QA47 new ' + qa.data.batch, inn: qa.user('OPERATOR').inn, company_phone: '+79991234567', offer_amount: '70000' }));
  expect(created.contractor_user_id).toBeTruthy();
  expect(created.offer_id).not.toBe(request.offers[0]);
});

test('QA47-28 manual offer amount/files persist and viewing deleted offers does not restore', async () => {
  const request = await qa.request('28_edit_' + Date.now());
  const offer = await qa.offer(request);
  await qa.ok('ECONOMIST', `/offers/${offer}`, 'PATCH', { offer_amount: 75000 });
  const file = await qa.unwrap(await qa.multipart('ECONOMIST', `/offers/${offer}/files`, { file: { name: 'offer.pdf', mimeType: 'application/pdf', buffer: pdf(request.id) } }));
  let workspace = await qa.ok('ECONOMIST', `/offers/${offer}/workspace`);
  expect(workspace.offer.offer_amount).toBe(75000);
  expect(workspace.offer.files.some((item: { id: number }) => item.id === file.file_id)).toBe(true);
  await qa.ok('ECONOMIST', `/offers/${offer}/files/${file.file_id}`, 'DELETE');
  await qa.ok('ECONOMIST', `/offers/${offer}/status`, 'PATCH', { status: 'deleted' });
  workspace = await qa.ok('PROJECT_MANAGER', `/offers/${offer}/workspace`);
  expect(workspace.offer.status).toBe('deleted');
  const ordinary = await qa.ok('ORDINARY', `/requests/${encoded(request.id)}/offers`, 'POST', { offer_amount: 82000 });
  const ordinaryFile = { name: 'ordinary.pdf', mimeType: 'application/pdf', buffer: pdf(request.id + 'ordinary') };
  const uploaded = await qa.unwrap(await qa.multipart('ORDINARY', `/offers/${ordinary.offer_id}/files`, { file: ordinaryFile }));
  await qa.denied('CONTRACTOR', `/offers/${ordinary.offer_id}/files/${uploaded.file_id}`, 'DELETE');
  expect((await qa.multipart('PROJECT_MANAGER', `/offers/${ordinary.offer_id}/files`, { file: ordinaryFile })).status()).toBe(403);
  await qa.ok('ECONOMIST', `/offers/${ordinary.offer_id}/status`, 'PATCH', { status: 'accepted' });
  expect((await qa.multipart('ORDINARY', `/offers/${ordinary.offer_id}/files`, { file: ordinaryFile })).status()).toBe(409);
  await qa.invalid('ORDINARY', `/offers/${ordinary.offer_id}`, 'PATCH', { offer_amount: 81000 });
});

test('QA47-29 accepting/rejecting selects the correct offer', async () => {
  const [first, second] = qa.state.requests.A1.offers;
  await qa.ok('ECONOMIST', `/offers/${first}/status`, 'PATCH', { status: 'accepted' });
  await qa.ok('ECONOMIST', `/offers/${second}/status`, 'PATCH', { status: 'rejected' });
  const offers = (await qa.ok('ECONOMIST', ownPath())).item.offers;
  expect(offers.find((item: { offer_id: number }) => item.offer_id === first).status).toBe('accepted');
  expect(offers.find((item: { offer_id: number }) => item.offer_id === second).status).toBe('rejected');
});

test('QA47-30 chat histories, read markers, attachments and text validation', async () => {
  const [first, second] = qa.state.requests.A1.offers;
  await qa.invalid('ECONOMIST', `/offers/${first}/messages`, 'POST', { text: '   ' });
  const message = 'QA47 chat ' + qa.data.batch + ' ' + Date.now();
  const sent = await qa.ok('ECONOMIST', `/offers/${first}/messages`, 'POST', { text: message });
  const messages = (await qa.ok('LEAD_ECONOMIST', `/offers/${first}/messages`)).items;
  expect(messages.filter((item: { text: string }) => item.text === message)).toHaveLength(1);
  expect((await qa.ok('ECONOMIST', `/offers/${second}/messages`)).items.some((item: { text: string }) => item.text === message)).toBe(false);
  await qa.ok('LEAD_ECONOMIST', `/offers/${first}/messages/read`, 'PATCH', { message_ids: [sent.message_id] });
  await qa.unwrap(await qa.multipart('ECONOMIST', `/offers/${first}/messages/attachments`, { text: 'QA47 attachment', files: { name: 'chat.pdf', mimeType: 'application/pdf', buffer: pdf(message) } }));
  const page = await qa.page('LEAD_ECONOMIST');
  await page.goto(`/offers/${first}/workspace`);
  await expect(page.getByRole('button', { name: 'Открыть чат', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Открыть чат', exact: true }).click();
  await expect(page.getByText(message, { exact: true })).toBeVisible();
  const sender = await qa.page('ECONOMIST');
  await sender.goto(`/offers/${first}/workspace`);
  await sender.getByRole('button', { name: 'Открыть чат', exact: true }).click();
  const realtimeText = message + ' realtime <b>plain text</b>';
  await sender.getByPlaceholder('Введите сообщение').fill(realtimeText);
  await sender.getByRole('button', { name: 'Отправить сообщение', exact: true }).click();
  await expect(page.getByText(realtimeText, { exact: true })).toBeVisible();
  await expect(page.locator('b').filter({ hasText: 'plain text' })).toHaveCount(0);
  await page.context().setOffline(true);
  const offlineText = message + ' while offline';
  await qa.ok('ECONOMIST', `/offers/${first}/messages`, 'POST', { text: offlineText });
  await page.context().setOffline(false);
  await expect(page.getByText(offlineText, { exact: true })).toBeVisible({ timeout: 20000 });
  const reply = message + ' after reconnect';
  await page.getByPlaceholder('Введите сообщение').fill(reply);
  await page.getByRole('button', { name: 'Отправить сообщение', exact: true }).click();
  await expect(sender.getByText(reply, { exact: true })).toBeVisible();
  const saved = (await qa.ok('ECONOMIST', `/offers/${first}/messages`)).items;
  for (const text of [realtimeText, offlineText, reply]) expect(saved.filter((item: { text: string }) => item.text === text)).toHaveLength(1);
  await qa.invalid('ECONOMIST', `/offers/${first}/messages`, 'POST', { text: 'x'.repeat(3001) });
  expect((await qa.multipart('ECONOMIST', `/offers/${first}/messages/attachments`, { text: 'x'.repeat(3001), files: { name: 'long.pdf', mimeType: 'application/pdf', buffer: pdf(message) } })).status()).toBe(409);
  expect((await qa.multipart('ECONOMIST', `/offers/${first}/messages/attachments`, { text: 'invalid attachment', files: { name: 'bad.exe', mimeType: 'application/octet-stream', buffer: Buffer.from('MZ invalid') } })).status()).toBe(422);
});

test('QA47-31 foreign request/offer/chat/file IDs do not bypass scope', async () => {
  const foreign = qa.state.requests.B;
  for (const role of ['ECONOMIST', 'LEAD_ECONOMIST', 'PROJECT_MANAGER']) {
    await qa.denied(role, '/requests/' + encoded(foreign.id));
    await qa.denied(role, `/offers/${foreign.offers[0]}/workspace`);
    await qa.denied(role, `/offers/${foreign.offers[0]}/messages`);
    await qa.denied(role, `/offers/${foreign.offers[0]}/messages`, 'POST', { text: 'forbidden' });
    await qa.denied(role, `/files/${foreign.file}/download`);
  }
  expect((await qa.api('ECONOMIST', '/requests/' + qa.data.batch + '_missing')).status()).toBe(404);
});

test('QA47-32 closure validates final amount, locks files and permits valid reopening', async () => {
  const plans = await qa.plans();
  await qa.ok('ECONOMIST', ownPath(), 'PATCH', { id_plan: plans.own });
  await qa.invalid('ECONOMIST', ownPath(), 'PATCH', { status: 'closed', final_amount: 85000 });
  await qa.ok('ECONOMIST', ownPath(), 'PATCH', { status: 'closed', final_amount: 80000 });
  const details = (await qa.ok('ECONOMIST', ownPath())).item;
  expect(details.status).toBe('closed'); expect(details.final_amount).toBe(80000);
  await qa.invalid('ECONOMIST', `/offers/${qa.state.requests.A1.offers[0]}`, 'PATCH', { offer_amount: 81000 });
  await qa.ok('ECONOMIST', ownPath(), 'PATCH', { status: 'open', deadline_at: new Date(Date.now() + 86400000 * 4).toISOString() });
  expect((await qa.ok('ECONOMIST', ownPath())).item.status).toBe('open');
  const zero = await qa.request('32_zero');
  await qa.ok('ECONOMIST', '/requests/' + encoded(zero.id), 'PATCH', { status: 'closed', final_amount: 100000 });
});

test('QA47-33 process and plan summaries stay scoped and consistent', async () => {
  const result = await qa.ok('PROJECT_MANAGER', '/dashboard/responsibility');
  expect(JSON.stringify(result)).not.toContain(qa.state.requests.B.id);
  const plans = await qa.ok('ECONOMIST', '/plans?period=' + new Date().toISOString().slice(0, 7));
  expect(JSON.stringify(plans)).not.toContain(qa.user('FOREIGN').login);
  const page = await qa.page('PROJECT_MANAGER');
  await page.goto('/pm-dashboard/savings');
  await expect(page.locator('main')).toBeVisible();
});

test('QA47-34 root plan creation is restricted to project manager/superadmin', async () => {
  await qa.plans();
  const now = new Date();
  const period = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + 1, 1)).toISOString().slice(0, 7);
  if (!qa.state.plans.future) {
    const root = await qa.ok('PROJECT_MANAGER', '/plans/root', 'POST', { period, name: 'QA47 future ' + qa.data.batch, plan_amount: 100000 });
    qa.state.plans.future = root.plan_id; qa.save();
  }
  for (const role of ['ADMIN', 'ECONOMIST', 'LEAD_ECONOMIST']) await qa.denied(role, '/plans/root', 'POST', { period, name: 'Forbidden root', plan_amount: 1000 });
});

test('QA47-35 delegated budgets, duplicate/budget validation and no-subordinate guard', async () => {
  const plans = await qa.plans();
  const period = new Date().toISOString().slice(0, 7);
  const root = (await qa.ok('PROJECT_MANAGER', `/plans/tree?period=${period}&root_user_id=${qa.user('PROJECT_MANAGER').login}`)).tree;
  expect(root.plan_amount).toBe(100000);
  const lead = root.children.find((item: { plan_id: number }) => item.plan_id === plans.lead);
  expect(lead.plan_amount).toBe(60000);
  expect(lead.children.find((item: { plan_id: number }) => item.plan_id === plans.own).plan_amount).toBe(30000);
  await qa.invalid('PROJECT_MANAGER', '/plans/delegate', 'POST', { parent_plan_id: plans.root, child_user_id: qa.user('SPARE').login, child_plan_amount: 100001 });
  await qa.invalid('PROJECT_MANAGER', '/plans/delegate', 'POST', { parent_plan_id: plans.root, child_user_id: qa.user('LEAD_ECONOMIST').login, child_plan_amount: 1000 });
  if (!plans.peer) {
    const peer = await qa.ok('PROJECT_MANAGER', '/plans/delegate', 'POST', { parent_plan_id: plans.root, child_user_id: qa.user('PEER').login, child_plan_amount: 1000 });
    plans.peer = peer.plan_id; qa.save();
  }
  expect([403, 409]).toContain((await qa.api('PEER', '/plans/subplan', 'POST', { parent_plan_id: plans.peer, name: 'Forbidden split', plan_amount: 100 })).status());
});

test('QA47-36 plan edits, empty deletion, dependency and future-close guards', async () => {
  const plans = await qa.plans();
  const today = new Date().toISOString().slice(0, 10);
  const child = await qa.ok('PROJECT_MANAGER', '/plans/subplan', 'POST', { parent_plan_id: plans.root, name: 'QA47 empty ' + Date.now(), period_start: today, plan_amount: 1000 });
  await qa.ok('PROJECT_MANAGER', `/plans/${child.plan_id}`, 'PATCH', { name: 'QA47 renamed', plan_amount: 1200 });
  await qa.ok('PROJECT_MANAGER', `/plans/${child.plan_id}`, 'DELETE');
  await qa.invalid('PROJECT_MANAGER', `/plans/${plans.lead}`, 'DELETE', {});
  await qa.invalid('PROJECT_MANAGER', `/plans/${plans.future}/close`, 'POST', {});
  const closable = await qa.ok('PROJECT_MANAGER', '/plans/subplan', 'POST', { parent_plan_id: plans.root, name: 'QA47 close ' + Date.now(), period_start: today, plan_amount: 1000 });
  await qa.ok('PROJECT_MANAGER', `/plans/${closable.plan_id}/close`, 'POST', {});
  await qa.invalid('PROJECT_MANAGER', `/plans/${closable.plan_id}`, 'PATCH', { plan_amount: 1200 });
});

test('QA47-37 tree/summary reads and foreign plan isolation', async () => {
  const period = new Date().toISOString().slice(0, 7);
  for (const role of ['ECONOMIST', 'LEAD_ECONOMIST', 'PROJECT_MANAGER', 'SUPERADMIN']) {
    await qa.ok(role, '/plans?period=' + period);
    await qa.ok(role, '/plans/my-summary?period=' + period);
  }
  await qa.denied('ECONOMIST', `/plans/tree?period=${period}&root_user_id=${qa.user('FOREIGN_MANAGER').login}`);
  await qa.ok('SUPERADMIN', `/plans/tree?period=${period}&root_user_id=${qa.user('FOREIGN_MANAGER').login}`);
});

test('QA47-38 personal name/phone persist while identity and role stay fixed', async () => {
  const role = 'ECONOMIST';
  const before = await qa.ok(role, '/auth/session');
  await qa.ok(role, '/users/me/profile', 'PATCH', { full_name: 'QA47 updated economist', phone: '+79997654321' });
  const profile = await qa.ok(role, '/users/me');
  expect(JSON.stringify(profile)).toContain('QA47 updated economist');
  const after = await qa.ok(role, '/auth/session');
  expect(after.login).toBe(before.login); expect(after.role_id).toBe(before.role_id);
  await qa.ok(role, '/users/me/profile', 'PATCH', { full_name: qa.name(role), phone: '+79991234567' });
});

test('QA47-39 own/subordinate unavailability validates dates, overlaps and authority', async () => {
  const start = new Date(Date.now() + 86400000 * 10).toISOString();
  const end = new Date(Date.now() + 86400000 * 12).toISOString();
  await qa.invalid('ECONOMIST', '/users/me/unavailability-period', 'POST', { status: 'vacation', started_at: end, ended_at: start });
  await qa.ok('ECONOMIST', '/users/me/unavailability-period', 'POST', { status: 'vacation', started_at: start, ended_at: end });
  await qa.invalid('ECONOMIST', '/users/me/unavailability-period', 'POST', { status: 'vacation', started_at: start, ended_at: end });
  const period = { status: 'business_trip', started_at: start, ended_at: end };
  await qa.ok('ECONOMIST', `/users/${qa.user('SUBORDINATE').login}/unavailability-period`, 'POST', period);
  await qa.denied('ECONOMIST', `/users/${qa.user('FOREIGN').login}/unavailability-period`, 'POST', period);
  await qa.denied('ADMIN', '/users/me/unavailability-period', 'POST', period);
});

test('QA47-40 department read grant/revoke from SA/admin/PM adds no mutations', async () => {
  const peer = '/requests/' + encoded(qa.state.requests.A2.id);
  for (const by of ['SUPERADMIN', 'ADMIN', 'PROJECT_MANAGER']) {
    try {
      await qa.grant(by, 'ECONOMIST', ['delegation.department.requests.read']);
      await qa.ok('ECONOMIST', peer);
      await qa.denied('ECONOMIST', '/requests/' + encoded(qa.state.requests.B.id));
      await qa.denied('ECONOMIST', peer, 'PATCH', { initial_amount: 110000 });
      await qa.denied('ECONOMIST', `/offers/${qa.state.requests.A2.offers[0]}`, 'PATCH', { offer_amount: 79000 });
      expect((await qa.multipart('ECONOMIST', `/offers/${qa.state.requests.A2.offers[0]}/files`, { file: { name: 'forbidden.pdf', mimeType: 'application/pdf', buffer: pdf(qa.data.batch + 'forbidden') } })).status()).toBe(403);
      await qa.denied('ECONOMIST', `/offers/${qa.state.requests.A2.offers[0]}/messages`, 'POST', { text: 'forbidden with read only' });
    } finally { await qa.grant(by, 'ECONOMIST', []); }
    await qa.denied('ECONOMIST', peer);
    await qa.ok('ECONOMIST', ownPath());
  }
});

test('QA47-41 independent department actions and revocation preserve base access', async () => {
  const peer = '/requests/' + encoded(qa.state.requests.A2.id), offer = qa.state.requests.A2.offers[0];
  await qa.ok('PEER', peer, 'PATCH', { status: 'open' });
  const codes = ['requests.update', 'requests.status_update', 'requests.assign', 'offers.update', 'offers.accept', 'offers.reject', 'chats.read', 'chats.send_message'];
  for (const code of codes) {
    try {
      await qa.grant('SUPERADMIN', 'ECONOMIST', ['delegation.department.requests.read', 'delegation.department.' + code]);
      if (code === 'requests.update') {
        await qa.ok('ECONOMIST', peer, 'PATCH', { initial_amount: 100001 });
        await qa.ok('ECONOMIST', peer, 'PATCH', { initial_amount: 100000 });
        await qa.denied('ECONOMIST', peer, 'PATCH', { status: 'review' });
      } else if (code === 'requests.status_update') {
        await qa.ok('ECONOMIST', peer, 'PATCH', { status: 'review' });
        await qa.ok('ECONOMIST', peer, 'PATCH', { status: 'open' });
        await qa.denied('ECONOMIST', peer, 'PATCH', { initial_amount: 110000 });
      } else if (code === 'requests.assign') {
        await qa.ok('ECONOMIST', peer, 'PATCH', { owner_user_id: qa.user('SUBORDINATE').login });
        await qa.ok('PROJECT_MANAGER', peer, 'PATCH', { owner_user_id: qa.user('PEER').login });
      } else if (code === 'offers.update') {
        await qa.ok('ECONOMIST', `/offers/${offer}`, 'PATCH', { offer_amount: 79000 });
        await qa.denied('ECONOMIST', `/offers/${offer}/status`, 'PATCH', { status: 'accepted' });
        await qa.ok('PEER', `/offers/${offer}`, 'PATCH', { offer_amount: 80000 });
      } else if (code === 'offers.accept' || code === 'offers.reject') {
        await qa.ok('ECONOMIST', `/offers/${offer}/status`, 'PATCH', { status: code.endsWith('accept') ? 'accepted' : 'rejected' });
        await qa.ok('PEER', `/offers/${offer}/status`, 'PATCH', { status: 'submitted' });
      } else if (code === 'chats.read') {
        await qa.ok('ECONOMIST', `/offers/${offer}/messages`);
        await qa.denied('ECONOMIST', `/offers/${offer}/messages`, 'POST', { text: 'forbidden read only' });
      } else {
        await qa.ok('ECONOMIST', `/offers/${offer}/messages`, 'POST', { text: 'QA47 delegated send ' + qa.data.batch });
        await qa.denied('ECONOMIST', `/offers/${qa.state.requests.B.offers[0]}/messages`, 'POST', { text: 'forbidden foreign delegated send' });
      }
    } finally { await qa.grant('SUPERADMIN', 'ECONOMIST', []); }
    await qa.denied('ECONOMIST', peer);
  }
});

test('QA47-42 analytics/plan grants extend only root A and keep management separate', async () => {
  const period = new Date().toISOString().slice(0, 7), plans = await qa.plans();
  try {
    await qa.grant('SUPERADMIN', 'ECONOMIST', ['delegation.department.dashboard.read']);
    expect(JSON.stringify(await qa.ok('ECONOMIST', '/dashboard/responsibility'))).toContain(qa.user('PEER').login);
    expect(JSON.stringify(await qa.ok('ECONOMIST', '/dashboard/responsibility'))).not.toContain(qa.user('FOREIGN').login);
    await qa.grant('SUPERADMIN', 'ECONOMIST', ['delegation.department.plans.read']);
    await qa.ok('ECONOMIST', `/plans/tree?period=${period}&root_user_id=${qa.user('PEER').login}`);
    await qa.denied('ECONOMIST', `/plans/${plans.peer}`, 'PATCH', { plan_amount: 1100 });
    await qa.grant('SUPERADMIN', 'ECONOMIST', ['delegation.department.plans.read', 'delegation.department.plans.manage']);
    await qa.ok('ECONOMIST', `/plans/${plans.peer}`, 'PATCH', { plan_amount: 1100 });
    await qa.ok('ECONOMIST', `/plans/${plans.peer}`, 'PATCH', { plan_amount: 1000 });
    await qa.denied('ECONOMIST', `/plans/tree?period=${period}&root_user_id=${qa.user('FOREIGN_MANAGER').login}`);
  } finally { await qa.grant('SUPERADMIN', 'ECONOMIST', []); }
});

test('QA47-43 self delegation and unauthorized/foreign-target delegation are forbidden', async () => {
  for (const role of five) await qa.denied(role, `/users/${qa.user(role).login}/delegations/department`, 'PUT', { access_codes: ['delegation.department.requests.read'] });
  for (const role of ['ECONOMIST', 'LEAD_ECONOMIST']) await qa.denied(role, `/users/${qa.user('SPARE').login}/delegations/department`, 'PUT', { access_codes: ['delegation.department.requests.read'] });
  await qa.denied('PROJECT_MANAGER', `/users/${qa.user('FOREIGN').login}/delegations/department`, 'PUT', { access_codes: ['delegation.department.requests.read'] });
});

test('QA47-44 contractor delegation targets lead economist and revokes cleanly', async () => {
  const path = `/contractors/${qa.user('HIDDEN').login}/status`;
  for (const by of ['SUPERADMIN', 'ADMIN']) {
    try {
      await qa.grant(by, 'LEAD_ECONOMIST', ['delegation.contractors.profile.status.update'], 'contractors');
      await qa.ok('LEAD_ECONOMIST', path, 'PATCH', { user_status: 'inactive' });
      await qa.ok('LEAD_ECONOMIST', path, 'PATCH', { user_status: 'active' });
    } finally { await qa.grant(by, 'LEAD_ECONOMIST', [], 'contractors'); }
    await qa.denied('LEAD_ECONOMIST', path, 'PATCH', { user_status: 'inactive' });
  }
  await qa.denied('ECONOMIST', `/users/${qa.user('LEAD_ECONOMIST').login}/delegations/contractors`, 'PUT', { access_codes: ['delegation.contractors.profile.status.update'] });
  await qa.denied('PROJECT_MANAGER', `/users/${qa.user('LEAD_ECONOMIST').login}/delegations/contractors`, 'PUT', { access_codes: ['delegation.contractors.profile.status.update'] });
});

test('QA47-45 internal notifications persist read state and reject another inbox ID', async () => {
  const offer = qa.state.requests.A1.offers[0];
  await qa.ok('LEAD_ECONOMIST', `/offers/${offer}/messages`, 'POST', { text: 'QA47 notification ' + Date.now() });
  await expect.poll(async () => (await qa.ok('ECONOMIST', '/notifications?limit=100')).items.length).toBeGreaterThan(0);
  const mine = (await qa.ok('ECONOMIST', '/notifications?limit=100')).items;
  await qa.ok('ECONOMIST', `/notifications/${mine[0].id}/read`, 'PATCH');
  const other = (await qa.ok('CONTRACTOR', '/notifications?limit=100')).items;
  expect(other.length).toBeGreaterThan(0);
  await qa.denied('ECONOMIST', `/notifications/${other[0].id}/read`, 'PATCH');
  await qa.ok('ECONOMIST', '/notifications/read-all', 'PATCH');
  expect((await qa.ok('ECONOMIST', '/notifications/unread-count')).count).toBe(0);
  await (await qa.page('ECONOMIST')).reload();
  expect((await qa.ok('ECONOMIST', '/notifications/unread-count')).count).toBe(0);
  const peerOffer = qa.state.requests.A2.offers[0];
  const spare = qa.user('SPARE').login;
  const sparePage = await qa.page('SPARE');
  const received: string[] = [];
  sparePage.on('websocket', (socket) => socket.on('framereceived', (frame) => received.push(String(frame.payload))));
  try {
    await qa.ok('SUPERADMIN', `/units/${qa.unit('A')}/members`, 'POST', { user_id: spare });
    await qa.ok('SPARE', `/offers/${peerOffer}/messages`);
    await qa.ok('PEER', `/offers/${peerOffer}/messages`, 'POST', { text: 'QA47 notification before opening chat ' + Date.now() });
    await expect.poll(async () => (await qa.ok('SPARE', '/notifications?limit=100')).items.some((item: { payload: { offer_id?: number } }) => item.payload.offer_id === peerOffer)).toBe(true);
    await sparePage.goto(`/offers/${peerOffer}/workspace`);
    await sparePage.getByRole('button', { name: 'Открыть чат', exact: true }).click();
    const visible = 'QA47 soon revoked access ' + Date.now();
    await qa.ok('PEER', `/offers/${peerOffer}/messages`, 'POST', { text: visible });
    await expect(sparePage.getByText(visible, { exact: true })).toBeVisible();
  } finally {
    await qa.ok('SUPERADMIN', `/units/${qa.unit('A')}/members/${spare}`, 'DELETE');
  }
  await qa.denied('SPARE', `/offers/${peerOffer}/workspace`);
  await qa.denied('SPARE', `/offers/${peerOffer}/messages`);
  const privateText = 'QA47 after membership revocation ' + Date.now();
  await qa.ok('PEER', `/offers/${peerOffer}/messages`, 'POST', { text: privateText });
  // Observe a bounded quiet period on the already open socket after revocation.
  await new Promise((resolve) => setTimeout(resolve, 1500));
  expect(received.some((payload) => payload.includes(privateText))).toBe(false);
});

test('QA47-46 feedback from all five roles validates and is visible only to superadmin', async () => {
  for (const role of five) {
    await qa.invalid(role, '/feedback', 'POST', { text: '   ' });
    const text = 'QA47 feedback ' + qa.data.batch + ' ' + role;
    const created = await qa.ok(role, '/feedback', 'POST', { text });
    const list = await qa.ok('SUPERADMIN', '/feedback?search=' + encoded(text) + '&limit=1&offset=0');
    expect(list.items).toHaveLength(1);
    expect(list.items[0]).toMatchObject({ id: created.feedback_id, author_user_id: qa.user(role).login, text });
    expect(list.items[0].created_at).toBeTruthy();
    if (role !== 'SUPERADMIN') await qa.denied(role, '/feedback');
  }
});

test('QA47-47 final identities, cleared grants and saved business links', async () => {
  await qa.grant('SUPERADMIN', 'ECONOMIST', []);
  await qa.grant('SUPERADMIN', 'LEAD_ECONOMIST', [], 'contractors');
  for (const role of five) {
    const session = await qa.ok(role, '/auth/session');
    expect(session).toMatchObject({ role_id: qa.user(role).role_id, status: 'active', business_access: true });
  }
  const request = await qa.ok('SUPERADMIN', ownPath());
  expect(request.item.owner_user_id).toBe(qa.user('ECONOMIST').login);
  expect(request.item.files.length).toBeGreaterThan(0);
  await qa.denied('ECONOMIST', '/requests/' + encoded(qa.state.requests.B.id));
  for (const role of five) {
    const page = await qa.page(role);
    await logoutFromUi(page);
    await expect(page.getByRole('heading', { name: 'Вход в AcomOfferDesk' })).toBeVisible();
    expect((await page.request.get('/api/v1/auth/session')).status()).toBe(401);
  }
});
