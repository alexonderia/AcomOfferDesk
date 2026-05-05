import fs from "node:fs/promises";
import path from "node:path";
import { chromium } from "playwright";

const BASE_URL = process.env.SCREENSHOT_BASE_URL || "http://localhost:8080";
const OUTPUT_DIR = process.env.SCREENSHOT_OUTPUT_DIR
  || path.resolve(process.cwd(), "..", "artifacts", "responsive-screens");

const VIEWPORTS = [
  { name: "mobile-375x812", width: 375, height: 812 },
  { name: "tablet-768x1024", width: 768, height: 1024 },
  { name: "desktop-1440x900", width: 1440, height: 900 },
];

const CONTEXT_BASE_OPTIONS = {
  extraHTTPHeaders: {
    "ngrok-skip-browser-warning": "true",
  },
};

const ROLES = [
  {
    key: "superadmin",
    username: "superadmin",
    password: "s18OouADqJ1vTEjpUFYCEFYhoLYWYGj4wPrNETyT07B",
    routes: ["/admin", "/requests", "/feedback", "/account"],
  },
  {
    key: "project_manager",
    username: "project_manager",
    password: "project_manager",
    routes: ["/pm-dashboard", "/pm-dashboard/savings", "/pm-dashboard/plan", "/requests", "/admin", "/feedback", "/account"],
  },
  {
    key: "lead_economist",
    username: "lead_economist",
    password: "lead_economist",
    routes: ["/pm-dashboard/plan", "/requests", "/admin", "/feedback", "/account"],
  },
  {
    key: "ooo_gvozd_27_04",
    username: "ooo_gvozd_27_04",
    password: "ooo_gvozd_27_04",
    routes: ["/requests?tab=my", "/requests?tab=open", "/feedback", "/account"],
  },
];

const CONTRACTOR_CANDIDATES = [
  { username: "contractor", password: "contractor" },
  { username: "contractor_1", password: "contractor_1" },
  { username: "test_contractor", password: "test_contractor" },
  { username: "user_contractor", password: "user_contractor" },
];

const CONTRACTOR_ROUTES = ["/requests?tab=my", "/requests?tab=open", "/feedback", "/account"];

const sanitize = (value) =>
  value
    .replace(/^\/+/, "")
    .replace(/[?&=]/g, "_")
    .replace(/[^a-zA-Z0-9._/-]+/g, "-")
    .replace(/\//g, "__")
    || "root";

const ensureDir = async (dir) => {
  await fs.mkdir(dir, { recursive: true });
};

const clearExistingPngs = async (dir) => {
  try {
    const entries = await fs.readdir(dir, { withFileTypes: true });
    await Promise.all(entries.map(async (entry) => {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        await clearExistingPngs(fullPath);
        const nested = await fs.readdir(fullPath);
        if (nested.length === 0) {
          await fs.rmdir(fullPath);
        }
        return;
      }
      if (entry.isFile() && entry.name.toLowerCase().endsWith(".png")) {
        await fs.unlink(fullPath);
      }
    }));
  } catch {
    // No previous output.
  }
};

const isLoginUrl = (url) => /\/login(?:\/|$)|\/auth\/login(?:\/|$)|\/iam\/realms\//i.test(url);

const isExpiredSessionScreenVisible = async (page) => {
  const reloginButton = page.getByRole("button", { name: /войти снова/i });
  const title = page.getByText(/вход в acomofferdesk/i);
  return (await reloginButton.count()) > 0 && (await title.count()) > 0;
};

const clickLoginCtaIfPresent = async (page) => {
  const reloginRegex = /войти снова|sign in again|login again/i;
  const ctas = [
    page.getByRole("button", { name: reloginRegex }).first(),
    page.getByRole("link", { name: reloginRegex }).first(),
    page.locator("button, a").filter({ hasText: reloginRegex }).first(),
  ];
  for (const cta of ctas) {
    try {
      if (await cta.isVisible({ timeout: 800 })) {
        await Promise.all([
          page.waitForLoadState("domcontentloaded").catch(() => {}),
          cta.click(),
        ]);
        await page.waitForTimeout(600);
        return true;
      }
    } catch {
      // Try next candidate.
    }
  }
  return false;
};

const ensureKeycloakFormVisible = async (page) => {
  if (await isExpiredSessionScreenVisible(page)) {
    await clickLoginCtaIfPresent(page);
  }
};

const login = async (page, username, password) => {
  const oidcLoginUrl = `${BASE_URL}/api/v1/auth/oidc/login?next_path=%2F&prompt=login&login_hint=${encodeURIComponent(username)}`;
  await page.goto(oidcLoginUrl, { waitUntil: "domcontentloaded" });
  await ensureKeycloakFormVisible(page);
  await clickLoginCtaIfPresent(page);

  const usernameLocators = [
    page.locator("#username, input[name='username'], input[autocomplete='username']"),
    page.getByLabel(/логин|email|username/i),
    page.getByPlaceholder(/логин|email|username/i),
  ];
  const passwordLocators = [
    page.locator("#password, input[name='password'], input[autocomplete='current-password'], input[type='password']"),
    page.getByLabel(/пароль|password/i),
    page.getByPlaceholder(/пароль|password/i),
  ];

  await fillFirstAvailable(page, usernameLocators, username, "username").catch(() => {});
  await fillFirstAvailable(page, passwordLocators, password, "password");

  const submitButton = page
    .locator("button[type='submit'], input[type='submit'], button[name='login']")
    .or(page.getByRole("button", { name: /войти|sign in|log in/i }))
    .first();

  await Promise.all([
    page.waitForLoadState("networkidle").catch(() => {}),
    submitButton.click(),
  ]);

  await page.waitForTimeout(1200);
  return !isLoginUrl(page.url());
};

const ensureLoggedIn = async (page, role) => {
  if (!isLoginUrl(page.url()) && !(await isExpiredSessionScreenVisible(page))) {
    return true;
  }
  return login(page, role.username, role.password);
};

const fillFirstAvailable = async (page, locators, value, fieldName) => {
  for (const locator of locators) {
    try {
      await locator.first().fill(value, { timeout: 5000 });
      return;
    } catch {
      // Try next locator.
    }
  }
  const debugBody = (await page.locator("body").innerText().catch(() => "")).slice(0, 240);
  await page.screenshot({
    path: path.join(OUTPUT_DIR, `debug-login-missing-${fieldName}.png`),
    fullPage: true,
  }).catch(() => {});
  throw new Error(`Unable to fill ${fieldName}: no matching visible input at ${page.url()} | body: ${debugBody}`);
};

const captureRoleScreenshots = async (browser, role) => {
  for (const viewport of VIEWPORTS) {
    const context = await browser.newContext({
      ...CONTEXT_BASE_OPTIONS,
      viewport: { width: viewport.width, height: viewport.height },
      deviceScaleFactor: 1,
    });
    const page = await context.newPage();
    const loggedIn = await login(page, role.username, role.password);
    if (!loggedIn) {
      await context.close();
      throw new Error(`Login failed for role "${role.key}" (${role.username})`);
    }

    const roleDir = path.join(OUTPUT_DIR, role.key, viewport.name);
    await ensureDir(roleDir);

    for (const route of role.routes) {
      const targetUrl = `${BASE_URL}${route}`;
      await page.goto(targetUrl, { waitUntil: "networkidle" });
      if (isLoginUrl(page.url()) || (await isExpiredSessionScreenVisible(page))) {
        const relogged = await ensureLoggedIn(page, role);
        if (!relogged) {
          throw new Error(`Re-login failed for role "${role.key}" on route "${route}"`);
        }
        await page.goto(targetUrl, { waitUntil: "networkidle" });
      }
      await page.waitForTimeout(700);
      const filename = `${sanitize(route)}.png`;
      const filepath = path.join(roleDir, filename);
      await page.screenshot({ path: filepath, fullPage: true });
      console.log(`[ok] ${role.key} ${viewport.name} ${route}`);
    }

    await context.close();
  }
};

const resolveContractorCreds = async (browser) => {
  const context = await browser.newContext({
    ...CONTEXT_BASE_OPTIONS,
    viewport: { width: 1280, height: 800 },
  });
  const page = await context.newPage();
  for (const candidate of CONTRACTOR_CANDIDATES) {
    const ok = await login(page, candidate.username, candidate.password);
    if (ok) {
      await context.close();
      return candidate;
    }
  }
  await context.close();
  return null;
};

const main = async () => {
  await ensureDir(OUTPUT_DIR);
  await clearExistingPngs(OUTPUT_DIR);
  const browser = await chromium.launch({ headless: true });
  try {
    for (const role of ROLES) {
      await captureRoleScreenshots(browser, role);
    }

    const contractorCreds = await resolveContractorCreds(browser);
    if (contractorCreds) {
      await captureRoleScreenshots(browser, {
        key: "contractor",
        username: contractorCreds.username,
        password: contractorCreds.password,
        routes: CONTRACTOR_ROUTES,
      });
      console.log(`[ok] contractor credentials resolved: ${contractorCreds.username}`);
    } else {
      console.warn("[warn] contractor credentials not found in candidates list");
    }
  } finally {
    await browser.close();
  }
};

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
