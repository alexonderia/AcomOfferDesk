import { expect, test, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';

const specificationBytes = readFileSync(new URL('../src/shared/lib/files/__fixtures__/preview.docx', import.meta.url));
const docxMime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';

const emails = ['registered@example.com', 'invite@example.com'];
const preview = {
  messages: emails.map((to_email, index) => ({
    to_email, kind: index ? 'invitation' : 'registered', subject: 'Новая заявка №17',
    html_content: `<html><body><h1>${index ? 'Приглашение' : 'Новая заявка'}</h1><p>Поставка оборудования</p></body></html>`,
    text_content: 'Поставка оборудования',
    attachments: [{ name: 'spec.txt', size_bytes: 12, download_url: '/api/v1/files/7/download', upload_index: null }],
  })), warnings: [],
};

const fixture = async (page: Page, options: { draft?: boolean; noMail?: boolean; canUpload?: boolean; canDelete?: boolean; hiddenKinds?: boolean; planName?: string } = {}) => {
  let sends = 0;
  let previews = 0;
  let specifications = 0;
  let failNextPreview = false;
  let failNextSend = false;
  let rejectNextSpecification = false;
  let sourceUploads = 0;
  let sourceDeletes = 0;
  let failNextSourceUpload = false;
  const sourceFiles: { id: number; name: string; download_url: string; is_specification_source: boolean | null; can_delete: boolean }[] = options.hiddenKinds ? [
    { id: 11, name: 'SourceForTZ.docx', download_url: '/api/v1/files/11/download', is_specification_source: true, can_delete: false },
    { id: 12, name: 'InternalAppendix.docx', download_url: '/api/v1/files/12/download', is_specification_source: false, can_delete: options.canDelete ?? false },
    { id: 13, name: 'Legacy.docx', download_url: '/api/v1/files/13/download', is_specification_source: null, can_delete: false },
  ] : [];
  const submitted: unknown[] = [];
  let releaseSend!: () => void;
  const sending = new Promise<void>(resolve => { releaseSend = resolve; });
  await page.route('**/api/**', async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    let body: unknown = { data: { items: [], total: 0, unread_count: 0 } };
    let status = 200;
    if (path === '/api/v1/auth/csrf') body = { csrf_token: 'fixture-csrf' };
    else if (path === '/api/v1/auth/session') body = { data: {
      user_id: 'fixture-economist', login: 'fixture-economist', role_id: 6, role: 'economist', status: 'active',
      business_access: true, email_enabled: !options.noMail,
      permissions: ['requests.read', 'requests.create', 'requests.update', 'requests.email_notifications.send', 'normative_files.read'],
    } };
    else if (path === '/api/v1/requests/17' && request.method() === 'GET') body = { data: { item: {
      request_id: '17', owner_user_id: 'fixture-economist', status: 'open', status_label: 'Открыта', initial_amount: 1000,
      deadline_at: '2100-05-20T23:59:59', description: 'Поставка оборудования', created_at: '2026-11-25T09:00:00Z', updated_at: '2026-11-25T09:00:00Z',
      files: [{ id: 7, name: 'spec.txt', download_url: '/api/v1/files/7/download', path: 'spec.txt' }], offers: [], stats: {},
      id_plan: options.planName ? 3 : null, plan_name: options.planName ?? null,
      actions: { can_view_details: true, can_view_amounts: true, can_edit: true, can_send_email_notifications: true, can_upload_files: options.canUpload ?? false, can_delete_files: options.canDelete ?? false },
    } } };
    else if (path.match(/\/source-files\/\d+$/) && request.method() === 'DELETE') {
      sourceDeletes++;
      const index = sourceFiles.findIndex((file) => file.id === Number(path.split('/').at(-1)));
      if (index < 0 || !sourceFiles[index].can_delete) { status = 409; body = { detail: 'Нельзя удалить исходник спецификации' }; }
      else { sourceFiles.splice(index, 1); body = { data: { request_id: '17', file_id: 12 } }; }
    }
    else if (path.endsWith('/source-files')) {
      if (request.method() === 'POST') {
        sourceUploads++;
        expect(request.postData()).toContain('filename="Appendix.docx"');
        if (failNextSourceUpload) { status = 503; body = { detail: 'Не удалось прикрепить закрытый исходник' }; failNextSourceUpload = false; }
        else {
          sourceFiles.push({ id: 9, name: 'Appendix.docx', download_url: '/api/v1/files/9/download', is_specification_source: false, can_delete: options.canDelete ?? false });
          body = { data: { request_id: '17', file_id: 9 } };
        }
      } else body = { files: sourceFiles };
    }
    else if (path === '/api/v1/requests/specification-preview') {
      specifications++;
      if (rejectNextSpecification) {
        rejectNextSpecification = false;
        await route.fulfill({ status: 422, contentType: 'application/json', body: JSON.stringify({
          detail: 'Файл «Alabuga_System_Tokens_Light.docx»: Office-файл повреждён: не удалось прочитать его внутреннюю структуру.',
          reason_code: 'invalid_office_document',
        }) });
        return;
      }
      expect(request.postData()).toContain('name="request_id"');
      expect(request.postData()).toContain('\r\n\r\n17\r\n');
      expect(request.postData()).toContain('name="extraction_indices"\r\n\r\n0\r\n');
      expect((request.postData()?.match(/name="extraction_indices"/g) ?? []).length).toBe(1);
      expect(request.postData()).toContain('name="public_source_indices"\r\n\r\n1\r\n');
      body = { name: 'Заявка на закупку 17.docx', mime_type: docxMime, content_base64: specificationBytes.toString('base64'),
        confirmation: 'fixture-confirmation', item_count: 1, used_ocr: false };
    }
    else if (path === '/api/v1/requests/check-id') body = { available: true };
    else if (path === '/api/v1/normative-files') body = { data: { items: [{ id: 1, file_id: 8, original_name: 'normative.txt', status: 'actual', download_url: '/api/v1/files/8/download' }] } };
    else if (path === '/api/v1/requests/email-preview' || path.endsWith('/email-notifications/preview')) {
      previews++;
      if (options.draft) expect(request.postDataJSON().files.map((file: { name: string }) => file.name))
        .toEqual(['Приложение.docx', 'Заявка на закупку 17.docx']);
      submitted.push(request.postDataJSON());
      if (failNextPreview) { status = 503; body = { detail: 'Не удалось подготовить проверку писем' }; failNextPreview = false; }
      else body = { data: options.draft ? { ...preview, messages: preview.messages.map((message) => ({
        ...message, attachments: (request.postDataJSON().files as { name: string; size_bytes: number }[])
          .map((file, index) => ({ ...file, upload_index: index, download_url: null })),
      })) } : preview };
    } else if ((path === '/api/v1/requests' && request.method() === 'POST') || path.endsWith('/email-notifications')) {
      sends++;
      submitted.push(options.draft ? request.postData() : request.postDataJSON());
      if (failNextSend) { status = 503; body = { detail: 'Не удалось отправить письма' }; failNextSend = false; }
      else { await sending; body = { data: { request_id: '17', file_ids: [7, 8], sent_to: emails } }; }
    } else if (/\/files\/\d+\/download$/.test(path)) {
      await route.fulfill({ status: 200, contentType: 'text/plain; charset=utf-8', body: 'Содержимое файла заявки' });
      return;
    } else if (path.includes('/ws/')) status = 403;
    await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) });
  });
  return { sends: () => sends, previews: () => previews, specifications: () => specifications, sourceUploads: () => sourceUploads, sourceDeletes: () => sourceDeletes, submitted, releaseSend,
    rejectSpecification: () => { rejectNextSpecification = true; },
    failSourceUpload: () => { failNextSourceUpload = true; },
    failPreview: () => { failNextPreview = true; }, failSend: () => { failNextSend = true; } };
};

test('additional mailing requires review, previews files, cancels safely and retries failed delivery', async ({ page }, testInfo) => {
  const state = await fixture(page);
  await page.goto('/requests/17');
  await page.getByRole('checkbox', { name: 'Дополнительная рассылка на электронную почту' }).check();
  await page.getByRole('textbox', { name: 'Дополнительные e-mail для рассылки' }).fill(emails.join(', '));
  state.failPreview();
  await page.getByRole('button', { name: 'Проверить и отправить', exact: true }).click();
  await expect(page.getByText('Не удалось подготовить проверку писем', { exact: true })).toBeVisible();
  expect(state.sends()).toBe(0);
  await expect(page.getByRole('dialog', { name: 'Проверка перед отправкой' })).not.toBeVisible();
  await page.getByRole('button', { name: 'Проверить и отправить', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Проверка перед отправкой' });
  await expect(dialog).toContainText('Поставка оборудования');
  await expect(dialog.getByRole('button', { name: 'Отмена', exact: true })).toBeFocused();
  expect(state.sends()).toBe(0);
  await dialog.getByRole('button', { name: 'Предпросмотр: spec.txt', exact: true }).first().click();
  await expect(page.getByRole('dialog', { name: 'Предпросмотр файла' })).toContainText('Содержимое файла заявки');
  await page.getByRole('button', { name: 'Закрыть предпросмотр' }).click();
  await dialog.getByRole('combobox', { name: 'Получатель и вариант письма' }).click();
  await page.getByRole('option', { name: 'invite@example.com — Заявка с приглашением', exact: true }).click();
  await expect(dialog).toContainText('Кому: invite@example.com');
  await expect(page.frameLocator('iframe[title="Письмо для invite@example.com"]').getByRole('heading', { name: 'Приглашение' })).toBeVisible();
  const bounds = await dialog.boundingBox();
  expect(bounds!.x).toBeGreaterThanOrEqual(0);
  expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(page.viewportSize()!.width);
  await page.screenshot({ path: testInfo.outputPath('email-review.png'), animations: 'disabled' });
  await page.keyboard.press('Escape');
  await expect(dialog).not.toBeVisible();
  expect(state.sends()).toBe(0);
  await page.getByRole('button', { name: 'Проверить и отправить', exact: true }).click();
  await dialog.getByRole('button', { name: 'Отмена', exact: true }).click();
  expect(state.sends()).toBe(0);
  await page.getByRole('button', { name: 'Проверить и отправить', exact: true }).click();
  state.failSend();
  await dialog.getByRole('button', { name: 'Подтвердить и отправить', exact: true }).click();
  await expect(page.getByText('Не удалось отправить письма', { exact: true })).toBeVisible();
  await expect(dialog.getByRole('button', { name: 'Подтвердить и отправить', exact: true })).toBeEnabled();
  await dialog.getByRole('button', { name: 'Отмена', exact: true }).focus();
  await page.keyboard.press('Tab');
  await page.keyboard.press('Enter');
  await expect.poll(state.sends).toBe(2);
  await expect(dialog.getByRole('button', { name: 'Отправка...', exact: true })).toBeDisabled();
  await expect(dialog.getByRole('button', { name: 'Отмена', exact: true })).toBeDisabled();
  await page.keyboard.press('Enter');
  await page.keyboard.press('Escape');
  await expect(dialog).toBeVisible();
  expect(state.sends()).toBe(2);
  state.releaseSend();
  await expect(dialog).not.toBeVisible();
  expect(state.submitted.at(-1)).toEqual({ additional_emails: emails });
});

for (const noMail of [false, true]) {
  test(`creating a request requires review and preserves local file preview (no mail: ${noMail})`, async ({ page }, testInfo) => {
    const state = await fixture(page, { draft: true, noMail });
    await page.goto('/requests/create');
    await page.getByRole('textbox', { name: 'Номер заявки', exact: true }).fill('17');
    await page.getByPlaceholder('Кратко опишите содержание заявки').fill('Поставка оборудования');
    await page.getByRole('textbox', { name: 'Сумма по ТЗ', exact: true }).fill('1000');
    await page.locator('input[type=file]').setInputFiles([
      { name: 'Договор.docx', mimeType: docxMime, buffer: specificationBytes },
      { name: 'Приложение.docx', mimeType: docxMime, buffer: specificationBytes },
    ]);
    const fileList = page.getByRole('list', { name: 'Файлы заявки', exact: true });
    await expect(fileList.getByRole('listitem')).toHaveCount(2);
    await expect(fileList.getByRole('checkbox')).toHaveCount(4);
    const extractContract = page.getByRole('checkbox', { name: 'Выделить спецификацию: Договор.docx', exact: true });
    await expect(extractContract).toBeChecked();
    await expect(page.getByRole('checkbox', { name: 'Выделить спецификацию: Приложение.docx', exact: true })).not.toBeChecked();
    await expect(page.getByRole('checkbox', { name: 'Скрыть от контрагентов: Договор.docx', exact: true })).toBeChecked();
    const hideAppendix = page.getByRole('checkbox', { name: 'Скрыть от контрагентов: Приложение.docx', exact: true });
    await expect(hideAppendix).toBeChecked();
    await hideAppendix.focus();
    await page.keyboard.press('Space');
    await expect(hideAppendix).not.toBeChecked();
    await expect(extractContract).toBeChecked();
    const listBounds = await fileList.boundingBox();
    expect(listBounds!.x + listBounds!.width).toBeLessThanOrEqual(page.viewportSize()!.width);
    await fileList.screenshot({ path: testInfo.outputPath('file-options-list.png'), animations: 'disabled' });
    await extractContract.uncheck();
    await page.getByRole('button', { name: 'Проверить и создать заявку', exact: true }).click();
    await expect(page.getByRole('alert').filter({ hasText: 'Выберите хотя бы один файл для формирования заявки' })).toBeVisible();
    expect(state.specifications()).toBe(0);
    await extractContract.check();
    if (!noMail) {
      await page.getByRole('checkbox', { name: 'Дополнительная рассылка на электронную почту' }).check();
      await page.getByRole('textbox', { name: 'Дополнительные e-mail для рассылки' }).fill(emails.join(', '));
    }
    const check = page.getByRole('button', { name: 'Проверить и создать заявку', exact: true });
    await check.click();
    const dialog = page.getByRole('dialog', { name: 'Проверка перед отправкой' });
    await expect(dialog).toContainText('Заявка №17');
    await expect(dialog).toContainText('Выделено позиций: 1');
    await expect(dialog).toContainText('Для формирования заявки: Договор.docx');
    await expect(dialog.getByRole('button', { name: 'Предпросмотр: Приложение.docx', exact: true }).first()).toBeVisible();
    expect(state.sends()).toBe(0);
    if (noMail) await expect(dialog).toContainText('Почтовый сервис отключён');
    await expect(dialog).toContainText('Исходники — доступны только сотрудникам');
    await dialog.getByRole('button', { name: 'Предпросмотр: Заявка на закупку 17.docx', exact: true }).first().click();
    await expect(page.frameLocator('iframe[title="Документ Заявка на закупку 17.docx"]').getByText('Preview document')).toBeVisible();
    await page.getByRole('button', { name: 'Закрыть предпросмотр' }).click();
    await dialog.getByRole('button', { name: 'Предпросмотр: Договор.docx', exact: true }).click();
    await expect(page.frameLocator('iframe[title="Документ Договор.docx"]').getByText('Preview document')).toBeVisible();
    await page.getByRole('button', { name: 'Закрыть предпросмотр' }).click();
    await dialog.getByRole('button', { name: 'Отмена', exact: true }).click();
    expect(state.sends()).toBe(0);
    await expect(hideAppendix).not.toBeChecked();
    await expect(page.getByRole('textbox', { name: 'Номер заявки', exact: true })).toHaveValue('17');
    await check.click();
    await dialog.getByRole('button', { name: 'Подтвердить и создать заявку', exact: true }).click();
    await expect.poll(state.sends).toBe(1);
    await expect(dialog.getByRole('button', { name: 'Отмена', exact: true })).toBeDisabled();
    state.releaseSend();
    await expect(page).toHaveURL(/\/requests$/);
    expect(state.specifications()).toBe(2);
    expect(state.previews()).toBe(noMail ? 0 : 2);
    const submitted = String(state.submitted.at(-1));
    expect(submitted).toContain('name="source_files"');
    expect(submitted).toContain('name="specification_confirmation"');
    expect(submitted).toContain('fixture-confirmation');
    expect(submitted).toContain('Приложение.docx');
  });
}

test('private originals accept additional files without extraction or public upload', async ({ page }, testInfo) => {
  const state = await fixture(page, { canUpload: true });
  await page.goto('/requests/17');
  const card = page.getByRole('region', { name: 'Карточка заявки №17', exact: true });
  await expect(card.getByRole('textbox', { name: 'План заявки', exact: true })).toHaveValue('Без плана');
  await expect(card.getByRole('checkbox', { name: /Выделить спецификацию/ })).toHaveCount(0);
  const add = card.getByRole('button', { name: 'Добавить скрытый файл', exact: true });
  await expect(add).toHaveCount(0);
  await card.getByRole('button', { name: 'Изменить', exact: true }).click();
  await expect(add).toBeEnabled();
  const selectFile = async () => {
    const choosing = page.waitForEvent('filechooser');
    await add.click();
    await (await choosing).setFiles({ name: 'Appendix.docx', mimeType: docxMime, buffer: specificationBytes });
  };
  await selectFile();
  expect(state.sourceUploads()).toBe(0);
  await card.getByRole('button', { name: 'Отмена', exact: true }).click();
  await expect(card.getByRole('button', { name: 'Appendix.docx', exact: true })).toHaveCount(0);
  expect(state.sourceUploads()).toBe(0);
  await card.getByRole('button', { name: 'Изменить', exact: true }).click();
  await selectFile();
  state.failSourceUpload();
  await card.getByRole('button', { name: 'Сохранить', exact: true }).click();
  await expect(page.getByRole('alert').filter({ hasText: 'Не удалось прикрепить закрытый исходник' })).toBeVisible();
  await expect(add).toBeEnabled();
  await card.getByRole('button', { name: 'Сохранить', exact: true }).click();
  await expect(card.getByRole('button', { name: 'Appendix.docx', exact: true })).toBeVisible();
  await expect(add).toHaveCount(0);
  await expect(page.getByText('Доступны сотрудникам с доступом к заявке. Контрагенты их не видят.', { exact: true })).toHaveCount(0);
  await card.getByRole('button', { name: 'О скрытых файлах заявки', exact: true }).click();
  const info = page.getByRole('tooltip');
  await expect(info).toContainText('Контрагенты их не видят');
  await expect(info).toContainText('Каждый файл — до 5 МБ');
  await expect(info).not.toContainText('Appendix.docx');
  await page.keyboard.press('Escape');
  await expect(info).not.toBeVisible();
  await card.getByRole('button', { name: 'Appendix.docx', exact: true }).focus();
  await expect(page.getByRole('tooltip')).toHaveText('Скрытое вложение');
  await card.getByRole('textbox', { name: 'План заявки', exact: true }).focus();
  await expect(page.getByRole('tooltip')).not.toBeVisible();
  const planBounds = await card.getByRole('textbox', { name: 'План заявки', exact: true }).boundingBox();
  const createdBounds = await card.getByText('Создана', { exact: true }).boundingBox();
  expect(planBounds!.y).toBeGreaterThan(createdBounds!.y);
  expect(state.sourceUploads()).toBe(2);
  expect(state.specifications()).toBe(0);
  expect(state.sends()).toBe(0);
  const bounds = await card.boundingBox();
  expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(page.viewportSize()!.width);
  await card.screenshot({ path: testInfo.outputPath('private-source-upload.png'), animations: 'disabled' });
});

test('read-only request does not offer private source upload', async ({ page }) => {
  await fixture(page);
  await page.goto('/requests/17');
  await expect(page.getByText('Поставка оборудования', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Добавить скрытый файл', exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Изменить', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Добавить скрытый файл', exact: true })).toHaveCount(0);
});

test('hidden attachments are deleted on save in edit mode while specification sources remain protected', async ({ page }) => {
  const state = await fixture(page, { hiddenKinds: true, canDelete: true, canUpload: true });
  await page.goto('/requests/17');
  const card = page.getByRole('region', { name: 'Карточка заявки №17', exact: true });
  const attachment = card.getByRole('button', { name: 'InternalAppendix.docx', exact: true });
  await attachment.focus();
  await page.keyboard.press('Delete');
  await expect(attachment).toBeVisible();
  await expect(card.getByRole('button', { name: 'Добавить скрытый файл', exact: true })).toHaveCount(0);
  await card.getByRole('button', { name: 'Изменить', exact: true }).click();
  for (const name of ['SourceForTZ.docx', 'Legacy.docx']) {
    const source = card.getByRole('button', { name, exact: true });
    await source.focus();
    await page.keyboard.press('Delete');
    await expect(source).toBeVisible();
  }
  await attachment.focus();
  await page.keyboard.press('Delete');
  await expect(attachment).toHaveCount(0);
  expect(state.sourceDeletes()).toBe(0);
  await card.getByRole('button', { name: 'Отмена', exact: true }).click();
  await expect(attachment).toBeVisible();
  expect(state.sourceDeletes()).toBe(0);
  await card.getByRole('button', { name: 'Изменить', exact: true }).click();
  await attachment.focus();
  await page.keyboard.press('Delete');
  const choosing = page.waitForEvent('filechooser');
  await card.getByRole('button', { name: 'Добавить скрытый файл', exact: true }).click();
  await (await choosing).setFiles({ name: 'Appendix.docx', mimeType: docxMime, buffer: specificationBytes });
  state.failSourceUpload();
  await card.getByRole('button', { name: 'Сохранить', exact: true }).click();
  await expect(page.getByRole('alert').filter({ hasText: 'Не удалось прикрепить закрытый исходник' })).toBeVisible();
  expect(state.sourceDeletes()).toBe(1);
  await card.getByRole('button', { name: 'Сохранить', exact: true }).click();
  await expect(card.getByRole('button', { name: 'Изменить', exact: true })).toBeVisible();
  await expect(attachment).toHaveCount(0);
  await expect(card.getByRole('button', { name: 'SourceForTZ.docx', exact: true })).toBeVisible();
  await expect(card.getByRole('button', { name: 'Legacy.docx', exact: true })).toBeVisible();
  expect(state.sourceDeletes()).toBe(1);
  expect(state.sourceUploads()).toBe(2);
  await expect(card.getByRole('button', { name: 'Appendix.docx', exact: true })).toBeVisible();
  expect(state.specifications()).toBe(0);
});

test('hidden files distinguish specification sources, ordinary attachments and legacy unknown purpose', async ({ page }) => {
  await fixture(page, { hiddenKinds: true, planName: 'План закупок оборудования' });
  await page.goto('/requests/17');
  const card = page.getByRole('region', { name: 'Карточка заявки №17', exact: true });
  await expect(card.getByText('Скрытые файлы заявки', { exact: true })).toBeVisible();
  await expect(card.getByRole('textbox', { name: 'План заявки', exact: true })).toHaveValue('План закупок оборудования');
  await card.getByRole('button', { name: 'О скрытых файлах заявки', exact: true }).focus();
  const info = page.getByRole('tooltip');
  await expect(info).not.toContainText('Назначение неизвестно');
  await page.keyboard.press('Escape');
  await expect(info).not.toBeVisible();
  for (const [name, label] of [['SourceForTZ.docx', 'Исходник для ТЗ'], ['InternalAppendix.docx', 'Скрытое вложение'], ['Legacy.docx', 'Назначение неизвестно']]) {
    await card.getByRole('button', { name, exact: true }).focus();
    await expect(page.getByRole('tooltip')).toHaveText(label);
    await card.getByRole('textbox', { name: 'План заявки', exact: true }).focus();
    await expect(page.getByRole('tooltip')).not.toBeVisible();
  }
  await card.getByRole('button', { name: 'Изменить', exact: true }).click();
  const plan = card.getByRole('combobox', { name: 'План заявки', exact: true });
  await expect(plan).toBeEnabled();
  await plan.focus();
  await page.keyboard.press('Space');
  await page.getByRole('option', { name: 'Без плана', exact: true }).click();
  await expect(plan).toHaveText('Без плана');
  await card.getByRole('button', { name: 'Отмена', exact: true }).click();
  await expect(card.getByRole('textbox', { name: 'План заявки', exact: true })).toHaveValue('План закупок оборудования');
});

test('file rejection identifies the failed attachment and keeps the form editable', async ({ page }, testInfo) => {
  const state = await fixture(page, { draft: true, noMail: true });
  state.rejectSpecification();
  await page.goto('/requests/create');
  await page.getByRole('textbox', { name: 'Номер заявки', exact: true }).fill('17');
  await page.getByRole('textbox', { name: 'Сумма по ТЗ', exact: true }).fill('1000');
  await page.locator('input[type=file]').setInputFiles([
    { name: 'Договор.docx', mimeType: docxMime, buffer: specificationBytes },
    { name: 'Alabuga_System_Tokens_Light.docx', mimeType: docxMime, buffer: specificationBytes },
  ]);
  const check = page.getByRole('button', { name: 'Проверить и создать заявку', exact: true });
  await check.click();
  const alert = page.getByRole('alert', { includeHidden: true }).filter({ hasText: 'Файл «Alabuga_System_Tokens_Light.docx»' });
  await expect(alert).toContainText('не удалось прочитать его внутреннюю структуру');
  await expect(check).toBeEnabled();
  await expect(page.getByRole('list', { name: 'Файлы заявки' }).getByRole('listitem')).toHaveCount(2);
  expect(state.sends()).toBe(0);
  await page.screenshot({ path: testInfo.outputPath('file-rejection.png'), animations: 'disabled' });
});
