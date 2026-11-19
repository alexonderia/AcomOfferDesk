/** Render existing components with labelled training data; never connect to business APIs. */
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
import fs from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { getGuideFixture } from './role_guide_fixture_responses.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'web');
const requireWeb = createRequire(path.join(web, 'package.json'));
const { createServer } = await import(pathToFileURL(requireWeb.resolve('vite')).href);
const { chromium } = requireWeb('playwright');
const screenshots = path.join(web, 'public', 'guides');
const checks = path.join(root, 'artifacts', 'role-guides');
await fs.mkdir(screenshots, { recursive: true });
await fs.mkdir(checks, { recursive: true });
const source = path.join(root, 'scripts', 'role_guide_preview.tsx').replaceAll('\\', '/');
const server = await createServer({
  configFile: path.join(web, 'vite.config.ts'), root: web,
  resolve: { dedupe: ['react', 'react-dom', '@mui/material', '@mui/icons-material', '@emotion/react', '@emotion/styled'] },
  server: { host: '127.0.0.1', port: 4197, strictPort: true, open: false, ws: false,
    fs: { allow: [web, path.join(root, 'scripts'), path.join(root, 'shared', 'fonts')] } },
  plugins: [{
    name: 'documentation-only-preview',
    configureServer(vite) {
      vite.middlewares.use(async (req, res, next) => {
        if (!req.url?.startsWith('/__guide_capture')) return next();
        try {
          const html = await vite.transformIndexHtml('/__guide_capture',
            `<!doctype html><html lang="ru"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head><body><div id="root"></div><script type="module" src="/@fs/${source}"></script></body></html>`);
          res.setHeader('Content-Type', 'text/html; charset=utf-8');
          res.end(html);
        } catch (error) { next(error); }
      });
    },
  }],
});

let browser;
try {
  await server.listen();
  browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1200, height: 1000 }, deviceScaleFactor: 1, locale: 'ru-RU', timezoneId: 'Europe/Moscow' });
  page.setDefaultTimeout(10000);
  page.setDefaultNavigationTimeout(30000);
  await page.clock.setFixedTime(new Date('2026-11-19T09:00:00Z'));
  const errors = [];
  page.on('pageerror', (error) => errors.push(`${new URL(page.url()).searchParams.get('view')}: ${error.message}`));
  const base = 'http://127.0.0.1:4197';
  const open = (view, role = 6) => page.goto(`${base}/__guide_capture?view=${view}&role=${role}`, { waitUntil: 'networkidle' });
  const dialog = () => page.getByRole('dialog').last();
  const frame = () => page.locator('[data-guide-preview]');
  const screenshotOptions = (filename) => ({
    path: path.join(screenshots, filename + '.png'),
    animations: 'disabled',
    style: '.MuiDialog-paper, .aod-card { border-radius: 0 !important; box-shadow: none !important; }',
  });
  const screenshot = (locator, filename) => locator.screenshot(screenshotOptions(filename));
  const fontReady = () => page.evaluate(() => document.fonts.ready);
  const documentPng = await page.evaluate(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 720;
    canvas.height = 360;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#fff';
    ctx.fillRect(0, 0, 720, 360);
    ctx.fillStyle = '#1c2e4a';
    ctx.font = 'bold 29px sans-serif';
    ctx.fillText('Учебная спецификация', 54, 74);
    ctx.font = '20px sans-serif';
    for (const [index, line] of [
      'Заявка УЧ-001 · Поставка оборудования',
      'Позиция: измерительный комплект',
      'Количество: 10 шт.',
      'Срок поставки: 10 рабочих дней',
      'Документ для примера в памятке',
    ].entries()) ctx.fillText(line, 54, 130 + index * 40);
    return canvas.toDataURL('image/png').split(',')[1];
  });
  const pythonInProject = path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
  const python = process.env.GUIDE_PYTHON ?? (await fs.access(pythonInProject).then(() => pythonInProject, () => 'python'));
  const loginPage = execFileSync(python, ['-c', [
    'import sys',
    'sys.path.insert(0, "iam")',
    'from iam_app.browser_pages import render_login_page',
    'sys.stdout.buffer.write(render_login_page().body)',
  ].join('; ')], { cwd: root });
  await page.routeWebSocket('**/*', (socket) => {
    const url = new URL(socket.url());
    if (url.host !== '127.0.0.1:4197' || url.pathname !== '/' || !url.searchParams.has('token')) {
      errors.push(`Unexpected WebSocket connection: ${url.host}${url.pathname}`);
    }
    socket.close();
  });
  await page.route('**/*', async (route) => {
    const url = new URL(route.request().url());
    const pathname = decodeURIComponent(url.pathname);
    if (url.origin !== base || route.request().method() !== 'GET') {
      errors.push(`Unexpected network request: ${route.request().method()} ${url.origin}${pathname}`);
      return route.abort();
    }
    if (pathname === '/api/v1/files/1/download') {
      return route.fulfill({ contentType: 'image/png', body: Buffer.from(documentPng, 'base64') });
    }
    if (pathname === '/__guide_login') return route.fulfill({ contentType: 'text/html; charset=utf-8', body: loginPage });
    const font = /^\/maintenance-assets\/fonts\/(alabuga-sans(?:-[a-z-]+)?\.(?:css|woff2))$/.exec(pathname);
    if (font) return route.fulfill({ path: path.join(root, 'shared', 'fonts', font[1]) });
    if (pathname.startsWith('/api/')) {
      const view = new URL(page.url()).searchParams.get('view') ?? '';
      const fixture = getGuideFixture(pathname, view);
      if (fixture) return route.fulfill({ json: fixture });
      errors.push(`Missing API fixture: ${pathname} in ${view}`);
      return route.abort();
    }
    if (pathname.startsWith('/iam/')) {
      errors.push(`Unexpected IAM route: ${pathname}`);
      return route.abort();
    }
    return route.continue();
  });

  const tableViews = ['requests-staff', 'requests-operator', 'requests-contractor', 'contractor-available'];
  const dialogViews = ['employee-scope', 'file-preview', 'manual-offer', 'invite', 'password-reset', 'feedback',
    'registration-review', 'admin-access', 'plan-create', 'request-create', 'request-submit'];
  const startViews = new Map([['guide-staff', 6], ['contractor-guide', 3]]);
  const expectedText = {
    hierarchy: 'Вложенная группа', 'hierarchy-actions': 'Вложенная группа',
    'employee-scope': 'Карточка сотрудника', password: 'Изменение пароля',
    'notifications-staff': 'Поступило новое КП', 'contractor-notifications': 'Ваше КП принято',
    'chat-staff': 'Поставка займёт 10 рабочих дней.', 'contractor-chat': 'Поставка займёт 10 рабочих дней.',
    'contractor-directory': 'Учебный поставщик', plan: 'Общий план', process: 'Общая диаграмма процесса заявок',
    users: 'training-economist', system: 'Режим работы', normative: 'Учебная спецификация.png',
    'offers-review': 'Наименование компании: Учебный поставщик', 'contractor-edit': 'Удалить отклик', 'contractor-files': 'Предложение поставщика.png',
  };
  await open('manifest');
  const guides = JSON.parse(await page.locator('#guide-manifest').textContent());
  const names = new Set();
  for (const guide of Object.values(guides)) {
    for (const chapter of guide.sections) {
      const images = chapter.blocks.filter((block) => block.type === 'image');
      if (!images.length) throw new Error(`Chapter has no screenshot: ${guide.title} / ${chapter.title}`);
      for (const block of images) names.add(path.basename(block.src, '.png'));
    }
  }
  const capture = async (name) => {
    console.log(`Capturing ${name}`);
    if (name === 'login') {
      await page.goto(`${base}/__guide_login`);
      await page.locator('input[name="login"]').waitFor();
      await fontReady();
      await screenshot(page.locator('.aod-card'), name);
      return;
    }
    if (startViews.has(name)) {
      await page.setViewportSize({ width: 640, height: 1000 });
      await open('intro', startViews.get(name));
      await page.getByLabel('Поиск по руководству').fill('пароль');
      await fontReady();
      const search = await dialog().locator('.MuiTextField-root').boundingBox();
      const contents = await page.getByRole('navigation', { name: 'Оглавление руководства' }).boundingBox();
      if (!search || !contents) throw new Error('Missing search or table of contents in guide preview');
      const top = Math.floor(search.y - 10);
      await page.screenshot({
        ...screenshotOptions(name),
        clip: {
          x: Math.floor(search.x - 10), y: top,
          width: Math.ceil(search.width + 20), height: Math.ceil(contents.y + contents.height - top + 8),
        },
      });
      await page.setViewportSize({ width: 1200, height: 1000 });
      return;
    }
    await open(name === 'request-submit' ? 'request-create' : name);
    if (tableViews.includes(name) || name === 'contractor-directory') {
      await page.getByRole('button').filter({ has: page.locator('[data-testid="SettingsOutlinedIcon"]') }).click();
      const hiddenColumns = name === 'contractor-directory'
        ? ['Телефон', 'E-mail', 'Телефон компании', 'E-mail компании']
        : ['Открыта', 'Закрыта', 'Последнее обновление'];
      for (const column of hiddenColumns) {
        const checkbox = page.getByRole('checkbox', { name: column, exact: true });
        if (await checkbox.count()) await checkbox.uncheck();
      }
      if (name === 'contractor-directory') await page.getByRole('checkbox', { name: 'Компания', exact: true }).check();
      await page.keyboard.press('Escape');
      await page.locator('.MuiPopover-root').waitFor({ state: 'detached' });
    }
    if (name === 'request-create' || name === 'request-submit') {
      await page.getByRole('textbox', { name: 'Номер заявки', exact: true }).fill('УЧ-003');
      await page.getByPlaceholder('Кратко опишите содержание заявки').fill('Учебная поставка оборудования');
      await page.getByLabel('Дата завершения сбора откликов', { exact: true }).waitFor();
      await page.getByLabel('Сумма по ТЗ', { exact: true }).fill('1000000');
      await page.getByRole('combobox', { name: /Нормативный документ/ }).click();
      await page.getByRole('option', { name: /Учебная спецификация\.png/ }).click();
      await page.locator('input[type=file]').setInputFiles({
        name: 'Учебная заявка.png', mimeType: 'image/png', buffer: Buffer.from(documentPng, 'base64'),
      });
      if (name === 'request-submit') {
        await page.getByRole('button', { name: 'Создать заявку', exact: true }).scrollIntoViewIfNeeded();
      }
    }
    if (name === 'assign-owner' || name === 'request-close' || name === 'contractor-edit' || name === 'contractor-files') {
      await page.getByRole('button', { name: 'Изменить', exact: true }).click();
    }
    if (name === 'assign-owner') {
      const owner = page.getByRole('combobox').filter({ hasText: 'Контакт по заявке' });
      await owner.click();
      await page.getByRole('option', { name: 'Борис' }).click();
      await page.getByRole('combobox').filter({ hasText: 'Борис' }).waitFor();
    }
    if (name === 'request-close') {
      await page.getByRole('combobox').filter({ hasText: 'Открыта' }).click();
      await page.getByRole('option', { name: 'Закрыта', exact: true }).click();
    }
    if (name === 'contractor-respond') {
      await page.getByRole('button', { name: 'Откликнуться', exact: true }).waitFor();
      await page.getByPlaceholder('Сумма КП, руб.').fill('850000');
    }
    if (name === 'contractor-files') {
      await page.getByRole('button', { name: 'Добавить файлы', exact: true }).waitFor();
    }
    if (name === 'admin-access') await page.getByText('training-economist', { exact: true }).first().click();
    if (name === 'registration-review') await page.getByText('training-supplier', { exact: true }).first().click();
    if (name === 'registration-review') await dialog().getByText('Ожидает проверки', { exact: true }).waitFor();
    if (name === 'password-reset') await page.getByRole('button', { name: 'Сбросить пароль', exact: true }).click();
    if (name === 'feedback') await page.getByRole('button', { name: /Обратная связь/ }).click();
    if (name === 'file-preview') await dialog().getByRole('img').waitFor();
    if (expectedText[name]) await page.getByText(expectedText[name], { exact: true }).first().waitFor();
    await fontReady();
    if (name === 'system') {
      const preview = await frame().boundingBox();
      const modes = await page.getByRole('region', { name: 'Доступные режимы работы' }).boundingBox();
      if (!preview || !modes) throw new Error('Missing system status summary');
      await page.screenshot({ ...screenshotOptions(name), clip: { ...preview, height: Math.floor(modes.y - preview.y - 8) } });
      return;
    }
    await screenshot(dialogViews.includes(name) ? dialog() : frame(), name);
  };
  if (!process.argv.includes('--check-only')) {
    for (const name of names) {
      try {
        await capture(name);
      } catch (error) {
        errors.push(`${name}: ${error.message}`);
        await page.screenshot({ path: path.join(checks, `failed-${name}.png`) });
      }
    }
  }
  if (errors.length) throw new Error(errors.join('\n'));
  await page.setViewportSize({ width: 1440, height: 1000 });
  await open('guide');
  await page.getByRole('dialog', { name: 'Руководство экономиста', exact: true }).waitFor();
  const checkDialogBounds = async (expected, state) => {
    const actual = await dialog().boundingBox();
    if (!actual || Object.keys(expected).some((key) => Math.abs(expected[key] - actual[key]) > 1)) {
      throw new Error(`Guide dialog moved or resized: ${state}`);
    }
  };
  const desktopBounds = await dialog().boundingBox();
  const contentsList = page.getByRole('navigation', { name: 'Оглавление руководства' }).getByRole('list');
  const article = page.getByRole('article');
  const scrollbar = await contentsList.evaluate((element) => {
    const style = getComputedStyle(element);
    return { width: style.scrollbarWidth, colors: style.scrollbarColor, scrollable: element.scrollHeight > element.clientHeight };
  });
  if (!scrollbar.scrollable || scrollbar.width !== 'thin' || !scrollbar.colors.endsWith('rgba(0, 0, 0, 0)')) {
    throw new Error('The table of contents must have a visible thumb and a transparent scrollbar track');
  }
  const contentsBounds = await contentsList.boundingBox();
  const articleBounds = await article.boundingBox();
  if (!contentsBounds || !articleBounds || Math.abs(contentsBounds.y + contentsBounds.height - articleBounds.y - articleBounds.height) > 1) {
    throw new Error('The desktop table of contents does not fill the reading area');
  }
  await page.getByRole('button', { name: 'Иерархия: что видно и чем можно управлять', exact: true }).focus();
  await page.keyboard.press('Enter');
  if (!await page.getByRole('article').evaluate((element) => element === document.activeElement)) throw new Error('Chapter keyboard navigation failed');
  await checkDialogBounds(desktopBounds, 'desktop chapter change');
  await page.screenshot({ path: path.join(checks, 'employee-desktop.png') });
  await page.getByLabel('Поиск по руководству').fill('сосед');
  if (!await page.getByRole('heading', { level: 2 }).count()) throw new Error('Employee guide search failed');
  await checkDialogBounds(desktopBounds, 'desktop search results');
  await page.getByLabel('Поиск по руководству').fill('неттакойглавы');
  await page.getByText('Ничего не найдено', { exact: true }).waitFor();
  await checkDialogBounds(desktopBounds, 'desktop empty search');
  await page.getByRole('button', { name: 'Очистить поиск' }).click();
  await page.getByLabel('Поиск по руководству').fill('кп');
  await page.getByRole('button', { name: 'Заявка: создать и вести работу', exact: true }).click();
  const checkImageSize = async (img) => {
    await img.evaluate(async (node) => {
      await node.decode();
      const { width, height } = node.getBoundingClientRect();
      const parentWidth = node.closest('article').clientWidth;
      const heightLimit = Math.min(innerHeight * 0.5, 480);
      if (width > Math.min(node.naturalWidth, parentWidth) + 1 || height > heightLimit + 1
        || Math.abs(height - width * node.naturalHeight / node.naturalWidth) > 1) {
        throw new Error('Guide image is enlarged, cropped or distorted');
      }
    });
  };
  await checkImageSize(page.getByRole('article').getByRole('img').first());
  await checkDialogBounds(desktopBounds, 'desktop image loaded');
  await page.screenshot({ path: path.join(checks, 'employee-desktop-search.png'), animations: 'disabled' });
  const listScroll = await contentsList.evaluate((element) => element.scrollTop);
  if (!await article.evaluate((element) => {
    element.scrollTop = element.scrollHeight;
    return element.scrollTop > 0;
  })) throw new Error('The desktop chapter must scroll inside the dialog');
  if (await contentsList.evaluate((element) => element.scrollTop) !== listScroll) {
    throw new Error('Scrolling the chapter moved the table of contents');
  }
  await page.getByRole('button', { name: 'Очистить поиск' }).click();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: path.join(checks, 'employee-mobile.png') });
  if (!await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)) throw new Error('Mobile viewport overflow');
  await page.goto('http://127.0.0.1:4197/__guide_capture?view=guide&role=3', { waitUntil: 'networkidle' });
  if (await page.getByRole('button', { name: /различия ролей|Иерархия|Планы:/ }).count()) throw new Error('Internal chapters visible to contractor');
  const mobileBounds = await dialog().boundingBox();
  await page.getByLabel('Поиск по руководству').fill('иерархия');
  await page.getByText('Ничего не найдено', { exact: true }).waitFor();
  await checkDialogBounds(mobileBounds, 'mobile empty search');
  await page.getByRole('button', { name: 'Очистить поиск' }).click();
  await page.getByRole('button', { name: 'Как получить доступ и войти', exact: true }).click();
  const contactLink = page.getByRole('link', { name: 'Обратитесь к контактному лицу в MAX' });
  if (new URL(await contactLink.getAttribute('href')).hostname !== 'max.ru') {
    throw new Error('The contractor guide must link to the contact in MAX');
  }
  await page.getByRole('button', { name: 'Мои заявки и статусы моих КП', exact: true }).click();
  await checkDialogBounds(mobileBounds, 'mobile chapter change');
  await page.screenshot({ path: path.join(checks, 'contractor-mobile.png') });
  await page.setViewportSize({ width: 390, height: 640 });
  const shortBounds = await dialog().boundingBox();
  if (!shortBounds || shortBounds.y < 0 || shortBounds.y + shortBounds.height > 641) {
    throw new Error('Guide dialog does not fit a short viewport');
  }
  await page.getByLabel('Поиск по руководству').fill('иерархия');
  await page.getByText('Ничего не найдено', { exact: true }).waitFor();
  await checkDialogBounds(shortBounds, 'short mobile empty search');
  await page.setViewportSize({ width: 390, height: 844 });
  for (const [role, guide] of Object.entries(guides)) {
    await open('guide', Number(role));
    for (const chapter of guide.sections) {
      await page.getByRole('button', { name: chapter.title, exact: true }).click();
      const images = page.getByRole('article').getByRole('img');
      if (await images.count() !== chapter.blocks.filter((block) => block.type === 'image').length) {
        throw new Error(`Incorrect number of screenshots in ${guide.title}: ${chapter.title}`);
      }
      for (const img of await images.all()) {
        await img.scrollIntoViewIfNeeded();
        await checkImageSize(img);
      }
    }
  }
  if (errors.length) throw new Error(errors.join('\n'));
  await fs.writeFile(path.join(checks, 'verification.json'), JSON.stringify({
    date: '2026-11-19', source: 'Current React and IAM views with labelled training data and intercepted read-only API fixtures',
    screenshots: [...names].map((name) => name + '.png'),
    chapterCount: Object.values(guides).reduce((count, guide) => count + guide.sections.length, 0),
    desktop: '1440x1000', mobile: '390x844', contractorIsolation: true, search: true, errors,
  }, null, 2));
  process.stdout.write('Guide screenshots and desktop/mobile checks completed. No business APIs used.\n');
} finally {
  await browser?.close();
  await server.close();
}

