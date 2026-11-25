import { expect, test } from '@playwright/test';

test('staff search and selection settle in the hierarchy assignment dialog', async ({ page }) => {
  const queries: string[] = [];
  let deletions = 0;
  let releaseDelete!: () => void;
  const deleteReady = new Promise<void>(resolve => { releaseDelete = resolve; });
  const staff = [{ user_id: 'employee_alpha', full_name: 'Альфа сотрудник', role_id: 6, role_name: 'Экономист', status: 'active' }];
  const actions = { can_create_child: true, can_update: true, can_delete: false, can_manage_members: true };
  const child = { unit_id: 101, name: 'Группа BR14', id_parent: 100, is_active: true, members: [] as typeof staff, children: [], actions };
  await page.route('**/api/**', async route => {
    const url = new URL(route.request().url());
    let body: unknown = { data: { items: [], total: 0, unread_count: 0 } };
    if (url.pathname === '/api/v1/auth/csrf') body = { csrf_token: 'fixture-csrf' };
    else if (url.pathname === '/api/v1/auth/session') body = { data: {
      user_id: 'fixture-manager', login: 'fixture-manager', role_id: 4, role: 'project_manager', status: 'active', business_access: true,
      permissions: ['units.read', 'units.members.manage'],
    } };
    else if (url.pathname === '/api/v1/units/tree') body = { data: { items: [{ unit_id: 100, name: 'Отдел BR14', id_parent: null, is_active: true, members: [], children: [child], actions }] } };
    else if (url.pathname === '/api/v1/units/101/members' && route.request().method() === 'POST') {
      child.members = [...staff];
      body = { data: staff[0] };
    }
    else if (url.pathname === '/api/v1/units/101/members/employee_alpha' && route.request().method() === 'DELETE') {
      deletions += 1;
      await deleteReady;
      child.members = [];
    }
    else if (url.pathname === '/api/v1/units/available-users') {
      const query = url.searchParams.get('search') ?? '';
      queries.push(query);
      body = { data: { items: staff.filter(user => user.user_id.includes(query) || user.full_name.includes(query)) } };
    }
    await route.fulfill({ status: url.pathname.includes('/ws/') ? 403 : 200, contentType: 'application/json', body: JSON.stringify(body) });
  });
  await page.goto('/admin/hierarchy');
  await page.getByRole('button', { name: 'Открыть схему объединения Группа BR14', exact: true }).first().click();
  await page.getByRole('button', { name: 'Добавить сотрудника в Группа BR14', exact: true }).first().click();
  const dialog = page.getByRole('dialog', { name: 'Добавить сотрудника в объединение', exact: true });
  const combo = dialog.getByRole('combobox');
  const searched = page.waitForResponse(response => new URL(response.url()).searchParams.get('search') === 'alpha');
  await combo.fill('alpha');
  await searched;
  const selectionQuery = page.waitForResponse(response => response.url().includes('/units/available-users'));
  await page.getByRole('option', { name: 'Альфа сотрудник (employee_alpha)', exact: true }).click();
  expect(new URL((await selectionQuery).url()).searchParams.has('search')).toBe(false);
  await expect(combo).toHaveValue('Альфа сотрудник (employee_alpha)');
  await expect(dialog.getByRole('button', { name: 'Добавить', exact: true })).toBeEnabled();
  expect(queries.some(query => query.includes('('))).toBe(false);
  await dialog.getByRole('button', { name: 'Добавить', exact: true }).click();
  await expect(dialog).not.toBeVisible();
  const detach = page.getByRole('button', { name: 'Открепить Альфа сотрудник', exact: true }).first();
  const confirmation = page.getByRole('dialog', { name: 'Открепление сотрудника', exact: true });
  await detach.click();
  await expect(confirmation).toContainText('Альфа сотрудник');
  await expect(confirmation).toContainText('Группа BR14');
  await expect(confirmation.getByRole('link', { name: 'ответственному в MAX' })).toHaveAttribute('href', /^https:\/\/max\.ru\//);
  await expect(confirmation.getByRole('button', { name: 'Отмена', exact: true })).toBeFocused();
  expect(deletions).toBe(0);
  await confirmation.getByRole('button', { name: 'Отмена', exact: true }).click();
  await expect(confirmation).not.toBeVisible();
  expect(deletions).toBe(0);
  await detach.click();
  await page.keyboard.press('Escape');
  await expect(confirmation).not.toBeVisible();
  expect(deletions).toBe(0);
  await detach.click();
  await expect(confirmation.getByRole('button', { name: 'Отмена', exact: true })).toBeFocused();
  await page.keyboard.press('Tab');
  await page.keyboard.press('Enter');
  await expect.poll(() => deletions).toBe(1);
  await expect(confirmation.getByRole('button', { name: 'Отмена', exact: true })).toBeDisabled();
  await expect(confirmation.getByRole('button', { name: 'Открепляем...', exact: true })).toBeDisabled();
  await page.keyboard.press('Escape');
  await expect(confirmation).toBeVisible();
  releaseDelete();
  await expect(confirmation).not.toBeVisible();
  await expect(detach).not.toBeVisible();
  expect(deletions).toBe(1);
});

test('hierarchy navigation and review deadline survive save and reload with isolated API fixtures', async ({ page }, testInfo) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  let saved: { deadline_at?: string; status?: string } | null = null;
  let statusWrites = 0;
  let releaseSave!: () => void;
  const saveReady = new Promise<void>(resolve => { releaseSave = resolve; });
  const item = {
    request_id: '17', owner_user_id: 'fixture-economist', owner_full_name: 'Тестовый экономист',
    status: 'review', status_label: 'На рассмотрении', initial_amount: 100, final_amount: 100,
    deadline_at: '2100-05-20T23:59:59', chosen_offer_id: null, id_plan: null, description: 'Проверка дедлайна',
    created_at: '2026-11-25T09:00:00Z', updated_at: '2026-11-25T09:00:00Z', files: [], offers: [], stats: {},
    actions: { can_view_details: true, can_view_amounts: true, can_edit: true, can_update_status: true },
  };
  // Every API request is fulfilled locally; these checks never use production data or credentials.
  await page.route('**/api/**', async route => {
    const request = route.request();
    const pathname = new URL(request.url()).pathname;
    let body: unknown = { data: { items: [], total: 0, unread_count: 0 } };
    let status = 200;
    if (pathname === '/api/v1/auth/csrf') body = { csrf_token: 'browser-fixture-csrf' };
    else if (pathname === '/api/v1/auth/session') body = { data: {
      user_id: 'fixture-economist', login: 'fixture-economist', role_id: 6, role: 'economist', status: 'active',
      business_access: true, email_enabled: false,
      permissions: ['requests.read', 'requests.update', 'units.read', 'users.read'],
    } };
    else if (pathname === '/api/v1/requests/17') {
      if (request.method() === 'PATCH') {
        saved = request.postDataJSON();
        if (saved?.status) {
          statusWrites += 1;
          await saveReady;
        }
        Object.assign(item, saved);
      }
      body = { data: { item } };
    } else if (pathname.includes('/ws/')) status = 403;
    await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) });
  });

  await page.goto('/admin/hierarchy');
  await page.getByRole('button', { name: 'Заявки', exact: true }).first().click();
  await expect(page).toHaveURL(/\/requests$/);
  await expect(page.getByText('Заявки не найдены.', { exact: true })).toBeVisible();
  await page.goBack();
  await expect(page).toHaveURL(/\/admin\/hierarchy$/);
  await expect(page.getByText('Все подразделения', { exact: true })).toBeVisible();
  await page.goForward();
  await expect(page.getByText('Заявки не найдены.', { exact: true })).toBeVisible();

  await page.goto('/requests/17');
  await page.getByRole('button', { name: 'Изменить', exact: true }).click();
  await page.locator('input[value="20.05.2100"]').click();
  await page.getByRole('button', { name: 'Следующий месяц', exact: true }).click();
  const day = page.getByRole('button', { name: '15', exact: true });
  await day.focus();
  await day.press('Enter');
  await day.press('Tab');
  await page.getByRole('button', { name: 'Готово', exact: true }).click();
  const save = page.getByRole('button', { name: 'Сохранить', exact: true });
  const bounds = await save.boundingBox();
  expect(bounds).not.toBeNull();
  expect(bounds!.x).toBeGreaterThanOrEqual(0);
  expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(page.viewportSize()!.width);
  await save.click();
  await expect(page.getByRole('button', { name: 'Изменить', exact: true })).toBeVisible();
  expect(saved).toEqual({ deadline_at: expect.stringContaining('2100-06-15') });
  await page.reload();
  await page.getByRole('button', { name: 'Изменить', exact: true }).click();
  await expect(page.locator('input[value="15.06.2100"]')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Сохранить', exact: true })).toBeDisabled();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  expect(errors).toEqual([]);
  await page.screenshot({ path: testInfo.outputPath('review-deadline.png'), fullPage: true });

  await page.getByRole('combobox').filter({ hasText: 'На рассмотрении' }).click();
  await page.getByRole('option', { name: 'Закрыта', exact: true }).click();
  await save.click();
  const confirmation = page.getByRole('dialog', { name: 'Изменение статуса заявки', exact: true });
  await expect(confirmation).toContainText('Закрыта');
  await expect(confirmation.getByRole('button', { name: 'Отмена', exact: true })).toBeFocused();
  expect(statusWrites).toBe(0);
  const dialogBounds = await confirmation.boundingBox();
  expect(dialogBounds!.x).toBeGreaterThanOrEqual(0);
  expect(dialogBounds!.x + dialogBounds!.width).toBeLessThanOrEqual(page.viewportSize()!.width);
  await confirmation.getByRole('button', { name: 'Отмена', exact: true }).click();
  await expect(confirmation).not.toBeVisible();
  expect(statusWrites).toBe(0);
  await save.click();
  await page.keyboard.press('Escape');
  await expect(confirmation).not.toBeVisible();
  expect(statusWrites).toBe(0);
  await save.click();
  await expect(confirmation.getByRole('button', { name: 'Отмена', exact: true })).toBeFocused();
  await page.keyboard.press('Tab');
  await page.keyboard.press('Enter');
  await expect.poll(() => statusWrites).toBe(1);
  await expect(confirmation.getByRole('button', { name: 'Сохраняем...', exact: true })).toBeDisabled();
  await expect(confirmation.getByRole('button', { name: 'Отмена', exact: true })).toBeDisabled();
  await page.keyboard.press('Escape');
  await expect(confirmation).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath('status-confirmation.png'), animations: 'disabled' });
  releaseSave();
  await expect(confirmation).not.toBeVisible();
  expect(statusWrites).toBe(1);
  expect(errors).toEqual([]);
});
