import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { expect, type APIResponse, type Browser, type BrowserContext, type Page } from '@playwright/test';
import { createPdfFixture, loginViaIam } from '../helpers';

type Identity = { login: string; password: string; role_id: number; inn: string; full_name?: string };
export type Dataset = { batch: string; users: Record<string, Identity>; units: Record<string, number> };
export type RequestData = { id: string; file: number; offers: number[] };
type State = { requests: Record<string, RequestData>; normative: number; plans: Record<string, number> };

export const datasetPath = process.env.E2E_QA47_CREDENTIALS;
export const dataset: Dataset | null = datasetPath ? JSON.parse(readFileSync(datasetPath, 'utf8')) : null;
export const encoded = encodeURIComponent;
export const pdf = (tag: string) => Buffer.concat([createPdfFixture(), Buffer.from(`% ${tag}\n`)]);

export class QA47 {
  readonly pages = new Map<string, Page>();
  readonly contexts: BrowserContext[] = [];
  readonly results: Array<{ number: number; title: string; status: string; duration: number }> = [];
  state: State = { requests: {}, normative: 0, plans: {} };
  constructor(readonly browser: Browser, readonly data: Dataset) {}
  user(role: string) { return this.data.users[role]; }
  name(role: string) { return this.user(role).full_name ?? 'QA47 ' + role; }
  unit(key: string) { return this.data.units[key]; }
  async page(role: string) {
    let page = this.pages.get(role);
    if (!page || page.isClosed()) {
      const context = await this.browser.newContext({ baseURL: 'http://localhost:8080', viewport: { width: 1440, height: 1000 } });
      this.contexts.push(context);
      page = await context.newPage();
      await loginViaIam(page, { username: this.user(role).login, password: this.user(role).password });
      this.pages.set(role, page);
    }
    return page;
  }
  async headers(page: Page) {
    const csrf = (await page.context().cookies()).find((item) => item.name === 'acom_csrf')?.value ?? '';
    return { 'X-CSRF-Token': csrf, Origin: 'http://localhost:8080' };
  }
  async api(role: string, path: string, method = 'GET', data?: object, refresh = true): Promise<APIResponse> {
    const page = await this.page(role);
    let response = await page.request.fetch('/api/v1' + path, { method, data, headers: await this.headers(page) });
    if (response.status() === 401 && refresh && path !== '/auth/refresh') {
      const refreshed = await page.request.post('/api/v1/auth/refresh', { headers: await this.headers(page) });
      if (refreshed.ok()) response = await page.request.fetch('/api/v1' + path, { method, data, headers: await this.headers(page) });
    }
    return response;
  }
  async ok(role: string, path: string, method = 'GET', data?: object) {
    return this.unwrap(await this.api(role, path, method, data));
  }
  async unwrap(response: APIResponse) {
    expect(response.ok(), `HTTP ${response.status()} ${(await response.text()).slice(0, 400)}`).toBe(true);
    return response.status() === 204 ? null : (await response.json()).data;
  }
  async denied(role: string, path: string, method = 'GET', data?: object) {
    const response = await this.api(role, path, method, data);
    expect([403, 404], `Expected authorization denial: ${path}`).toContain(response.status());
  }
  async invalid(role: string, path: string, method: string, data: object) {
    expect([409, 422], `Expected validation failure: ${path}`).toContain((await this.api(role, path, method, data)).status());
  }
  async multipart(role: string, path: string, fields: Record<string, string | { name: string; mimeType: string; buffer: Buffer }>) {
    const page = await this.page(role);
    await this.ok(role, '/auth/session');
    return page.request.post('/api/v1' + path, { headers: await this.headers(page), multipart: fields });
  }
  async request(key: string, role = 'ECONOMIST', hidden?: string[]) {
    if (this.state.requests[key]) return this.state.requests[key];
    const id = this.data.batch + '_' + key;
    const response = await this.multipart(role, '/requests', {
      id, initial_amount: '100000', deadline_at: new Date(Date.now() + 86400000 * 3).toISOString(),
      normative_file_id: String(this.state.normative), description: 'QA47 ' + key,
      ...(hidden?.length ? { hidden_contractor_ids: hidden[0] } : {}),
      files: { name: key + '.pdf', mimeType: 'application/pdf', buffer: pdf(id) }
    });
    const result = await this.unwrap(response);
    const details = await this.ok(role, '/requests/' + encoded(id));
    const created: RequestData = { id: result.request_id, file: details.item.files.find((file: { name: string }) => file.name === key + '.pdf')?.id ?? details.item.files[0].id, offers: [] };
    this.state.requests[key] = created;
    this.save();
    return created;
  }
  async offer(request: RequestData, contractor = 'CONTRACTOR', amount = 80000, role = 'ECONOMIST') {
    const response = await this.multipart(role, `/requests/${encoded(request.id)}/offers/manual`, { contractor_mode: 'existing', contractor_user_id: this.user(contractor).login, offer_amount: String(amount) });
    const data = await this.unwrap(response);
    request.offers.push(data.offer_id);
    this.save();
    return data.offer_id as number;
  }
  async grant(by: string, target: string, codes: string[], family = 'department') {
    await this.ok(by, `/users/${this.user(target).login}/delegations/${family}`, 'PUT', { access_codes: codes });
    const targetPage = await this.page(target);
    await this.unwrap(await targetPage.request.post('/api/v1/auth/refresh', { headers: await this.headers(targetPage) }));
  }
  async plans() {
    if (this.state.plans.own) return this.state.plans;
    const period = new Date().toISOString().slice(0, 7);
    const root = await this.ok('PROJECT_MANAGER', '/plans/root', 'POST', { period, name: 'QA47 root ' + this.data.batch, plan_amount: 100000 });
    const lead = await this.ok('PROJECT_MANAGER', '/plans/delegate', 'POST', { parent_plan_id: root.plan_id, child_user_id: this.user('LEAD_ECONOMIST').login, child_plan_amount: 60000 });
    const own = await this.ok('LEAD_ECONOMIST', '/plans/delegate', 'POST', { parent_plan_id: lead.plan_id, child_user_id: this.user('ECONOMIST').login, child_plan_amount: 30000 });
    const foreign = await this.ok('FOREIGN_MANAGER', '/plans/root', 'POST', { period, name: 'QA47 foreign ' + this.data.batch, plan_amount: 100000 });
    this.state.plans = { root: root.plan_id, lead: lead.plan_id, own: own.plan_id, foreign: foreign.plan_id };
    this.save();
    return this.state.plans;
  }
  save() {
    writeFileSync(join(dirname(datasetPath!), 'qa47-state.json'), JSON.stringify({ batch: this.data.batch, ...this.state }, null, 2));
  }
  async setup() {
    const statePath = join(dirname(datasetPath!), 'qa47-state.json');
    try {
      const cached = JSON.parse(readFileSync(statePath, 'utf8'));
      if (cached.batch === this.data.batch) this.state = cached;
    } catch { /* First run of this isolated dataset. */ }
    expect((await this.ok('SUPERADMIN', '/auth/capabilities')).email_enabled).toBe(false);
    if (this.data.users.FOREIGN_MANAGER) {
      const manager = this.user('FOREIGN_MANAGER');
      const users = (await this.ok('SUPERADMIN', '/users')).items;
      if (!users.some((user: { user_id: string }) => user.user_id === manager.login)) {
        await this.ok('SUPERADMIN', '/users/register', 'POST', { login: manager.login, role_id: manager.role_id, unit_id: this.unit('B'), full_name: 'QA47 FOREIGN_MANAGER', password: manager.password, password_confirmation: manager.password });
      }
    }
    const files = (await this.ok('ECONOMIST', '/normative-files?status=actual')).items;
    this.state.normative ||= files[0].id;
    const own = await this.request('A1');
    if (!own.offers.length) { await this.offer(own); await this.offer(own, 'HIDDEN', 90000); }
    await this.request('A11', 'SUBORDINATE');
    const peer = await this.request('A2', 'PEER');
    if (!peer.offers.length) await this.offer(peer, 'CONTRACTOR', 80000, 'PEER');
    const foreign = await this.request('B', 'FOREIGN');
    if (!foreign.offers.length) await this.offer(foreign, 'FOREIGN_CONTRACTOR', 70000, 'FOREIGN');
    this.save();
  }
  async close() {
    await Promise.all(this.contexts.map((context) => context.close()));
  }
}
