import fs from 'node:fs/promises';
import path from 'node:path';
import { chromium, devices } from 'playwright';

const baseUrl = process.env.BASE_URL ?? 'http://localhost:8080';
const outRoot = path.resolve(process.cwd(), 'artifacts', 'screenshots', 'roles');

const users = [
  { name: 'superadmin', login: 'superadmin', password: 's18OouADqJ1vTEjpUFYCEFYhoLYWYGj4wPrNETyT07B' },
  { name: 'project_manager', login: 'project_manager', password: 'project_manager' },
  { name: 'lead_economist', login: 'lead_economist', password: 'lead_economist' },
  { name: 'contractor', login: 'ooo_gvozd_27_04', password: 'ooo_gvozd_27_04' }
];

const viewports = [
  { name: 'desktop', viewport: { width: 1440, height: 960 } },
  { name: 'tablet', viewport: { width: 834, height: 1112 } },
  { name: 'mobile', device: devices['iPhone 13'] }
];

const navTargetsByRole = {
  superadmin: ['/admin', '/requests', '/pm-dashboard', '/pm-dashboard/savings', '/pm-dashboard/plan', '/feedback'],
  project_manager: ['/pm-dashboard', '/pm-dashboard/savings', '/pm-dashboard/plan', '/requests', '/admin'],
  lead_economist: ['/pm-dashboard', '/pm-dashboard/savings', '/pm-dashboard/plan', '/requests', '/admin'],
  contractor: ['/requests']
};

async function ensureDir(dir) {
  await fs.mkdir(dir, { recursive: true });
}

async function login(page, login, password) {
  for (let attempt = 1; attempt <= 4; attempt += 1) {
    await page.goto(`${baseUrl}/api/v1/auth/oidc/login?next_path=%2F&force_prompt=1`, { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle', { timeout: 60000 }).catch(() => {});

    const isAppPage = () => /\/(requests|admin|pm-dashboard|account)(\/|$)/.test(new URL(page.url()).pathname);
    if (isAppPage()) {
      return;
    }

    const usernameInput = page.locator('#username, input[name="username"], input[type="text"]').first();
    const hasUsername = await usernameInput.isVisible({ timeout: 15000 }).catch(() => false);
    if (!hasUsername) {
      if (attempt < 4) {
        await page.waitForTimeout(1500);
        continue;
      }
      throw new Error(`Login form not found at URL: ${page.url()}`);
    }
    await usernameInput.fill(login);

    const passwordInput = page.locator('#password, input[name="password"], input[type="password"]').first();
    await passwordInput.fill(password);

    const submitButton = page.locator('#kc-login, button[type="submit"], input[type="submit"]').first();
    await Promise.all([
      page.waitForLoadState('domcontentloaded', { timeout: 60000 }).catch(() => {}),
      submitButton.click()
    ]);

    await page.waitForLoadState('networkidle', { timeout: 60000 }).catch(() => {});
    await page.waitForTimeout(2000);
    return;
  }
}

async function captureForUser(browser, user) {
  const userDir = path.join(outRoot, user.name);
  await ensureDir(userDir);

  for (const vp of viewports) {
    const context = await browser.newContext(
      vp.device
        ? { ...vp.device, baseURL: baseUrl }
        : { viewport: vp.viewport, baseURL: baseUrl }
    );
    await context.setExtraHTTPHeaders({ 'ngrok-skip-browser-warning': '1' });
    const page = await context.newPage();
    await login(page, user.login, user.password);

    const targets = navTargetsByRole[user.name] ?? ['/requests'];
    for (const target of targets) {
      await page.goto(`${baseUrl}${target}`, { waitUntil: 'domcontentloaded' });
      await page.waitForLoadState('networkidle', { timeout: 45000 }).catch(() => {});
      await page.waitForTimeout(1200);

      const safeTarget = target.replaceAll('/', '_').replace(/^_+/, '') || 'home';
      await page.screenshot({ path: path.join(userDir, `${safeTarget}__${vp.name}.png`), fullPage: true });

      const tableBtn = page.locator('button:has-text("Таблица"), [role="button"]:has-text("Таблица")').first();
      const cardsBtn = page.locator('button:has-text("Карточки"), [role="button"]:has-text("Карточки")').first();
      const hasViewToggle = await cardsBtn.isVisible({ timeout: 2500 }).catch(() => false);
      if (hasViewToggle) {
        await tableBtn.click({ timeout: 5000 }).catch(() => {});
        await page.waitForTimeout(600);
        await page.screenshot({
          path: path.join(userDir, `${safeTarget}__table__${vp.name}.png`),
          fullPage: true
        });

        await cardsBtn.click({ timeout: 5000 }).catch(() => {});
        await page.waitForTimeout(600);
        await page.screenshot({
          path: path.join(userDir, `${safeTarget}__cards__${vp.name}.png`),
          fullPage: true
        });
      }
    }
    await context.close();
  }
}

async function main() {
  await ensureDir(outRoot);
  const browser = await chromium.launch({ headless: true });
  try {
    for (const user of users) {
      let success = false;
      let lastError = null;
      for (let attempt = 1; attempt <= 3; attempt += 1) {
        try {
          await captureForUser(browser, user);
          process.stdout.write(`Captured: ${user.name}\n`);
          success = true;
          break;
        } catch (error) {
          lastError = error;
          process.stdout.write(`Retry ${attempt}/3 failed for ${user.name}\n`);
          await new Promise((resolve) => setTimeout(resolve, 1500));
        }
      }
      if (!success && lastError) {
        throw lastError;
      }
    }
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
