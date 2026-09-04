import { afterEach, describe, expect, it, vi } from 'vitest';

import { apiFetch, fetchJson, setAuthRuntime, type AuthRefreshResult } from './client';

const jsonResponse = (status: number, body: unknown = {}) => new Response(
  JSON.stringify(body),
  { status, headers: { 'Content-Type': 'application/json' } }
);

describe('api client upload reason_code handling', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    setAuthRuntime(null);
  });

  it('prefers upload reason_code message over generic detail fallback', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          detail: 'Произошла ошибка. Попробуйте повторить действие.',
          reason_code: 'empty_file',
        }),
        {
          status: 422,
          headers: { 'Content-Type': 'application/json' },
        }
      )
    );

    await expect(
      fetchJson('/api/v1/requests/10/files', { method: 'POST', body: new FormData() }, 'Ошибка прикрепления файла')
    ).rejects.toThrow('Файл пустой.');
  });

  it('prefers upload reason_code message over not-found detail fallback', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          detail: 'Данные не найдены или были удалены.',
          reason_code: 'invalid_pdf',
        }),
        {
          status: 422,
          headers: { 'Content-Type': 'application/json' },
        }
      )
    );

    await expect(
      fetchJson('/api/v1/requests/10/files', { method: 'POST', body: new FormData() }, 'Ошибка прикрепления файла')
    ).rejects.toThrow('PDF-файл поврежден или не читается.');
  });
});

describe('api client silent session refresh', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    setAuthRuntime(null);
  });

  it('retries a protected request once after a successful silent refresh', async () => {
    const refresh = vi.fn<() => Promise<AuthRefreshResult>>().mockResolvedValue({ kind: 'success' });
    const forceLogout = vi.fn();
    setAuthRuntime({
      refresh,
      forceLogout,
      canAttemptSilentRefresh: () => true,
    });
    const fetchMock = vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(jsonResponse(401))
      .mockResolvedValueOnce(jsonResponse(200, { ok: true }));

    const response = await apiFetch('/api/v1/requests/10');

    expect(response.status).toBe(200);
    expect(refresh).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(forceLogout).not.toHaveBeenCalled();
  });

  it('joins parallel 401 retries to the runtime single-flight refresh', async () => {
    let resolveRefresh: (result: AuthRefreshResult) => void = () => undefined;
    const activeRefresh = new Promise<AuthRefreshResult>((resolve) => {
      resolveRefresh = resolve;
    });
    const startRefresh = vi.fn(() => activeRefresh);
    let refreshPromise: Promise<AuthRefreshResult> | null = null;
    const refresh = vi.fn(() => {
      refreshPromise ??= startRefresh();
      return refreshPromise;
    });
    setAuthRuntime({
      refresh,
      forceLogout: vi.fn(),
      canAttemptSilentRefresh: () => true,
    });
    let requestCount = 0;
    vi.spyOn(globalThis, 'fetch').mockImplementation(async () => {
      requestCount += 1;
      return requestCount <= 3 ? jsonResponse(401) : jsonResponse(200, { ok: true });
    });

    const requests = [
      apiFetch('/api/v1/requests/1'),
      apiFetch('/api/v1/requests/2'),
      apiFetch('/api/v1/requests/3'),
    ];
    await vi.waitFor(() => expect(startRefresh).toHaveBeenCalledTimes(1));
    resolveRefresh({ kind: 'success' });

    await expect(Promise.all(requests)).resolves.toHaveLength(3);
    expect(requestCount).toBe(6);
  });

  it('does not retry or log out after a transient refresh failure', async () => {
    const refresh = vi.fn<() => Promise<AuthRefreshResult>>().mockResolvedValue({ kind: 'unavailable' });
    const forceLogout = vi.fn();
    setAuthRuntime({
      refresh,
      forceLogout,
      canAttemptSilentRefresh: () => true,
    });
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(401));

    const response = await apiFetch('/api/v1/requests/10');

    expect(response.status).toBe(401);
    expect(refresh).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(forceLogout).not.toHaveBeenCalled();
  });

  it('logs out after a terminal refresh failure without retrying the original request', async () => {
    const refresh = vi.fn<() => Promise<AuthRefreshResult>>().mockResolvedValue({ kind: 'terminal' });
    const forceLogout = vi.fn();
    setAuthRuntime({
      refresh,
      forceLogout,
      canAttemptSilentRefresh: () => true,
    });
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(401));

    const response = await apiFetch('/api/v1/requests/10');

    expect(response.status).toBe(401);
    expect(refresh).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(forceLogout).toHaveBeenCalledTimes(1);
  });

  it('never tries to refresh the refresh endpoint itself', async () => {
    const refresh = vi.fn<() => Promise<AuthRefreshResult>>();
    setAuthRuntime({
      refresh,
      forceLogout: vi.fn(),
      canAttemptSilentRefresh: () => true,
    });
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(401));

    const response = await apiFetch('/api/v1/auth/refresh', { method: 'POST' });

    expect(response.status).toBe(401);
    expect(refresh).not.toHaveBeenCalled();
  });
});
