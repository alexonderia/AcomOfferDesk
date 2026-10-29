import { afterEach, describe, expect, it, vi } from 'vitest';

import { clearIamBrowserSession, logoutWebSession, refreshWebSession } from './loginWebUser';

const jsonResponse = (status: number, body: unknown = {}) => new Response(
  JSON.stringify(body),
  { status, headers: { 'Content-Type': 'application/json' } }
);

describe('refreshWebSession', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    document.cookie = 'acom_csrf=; Max-Age=0; path=/';
  });

  it('uses the existing CSRF cookie and returns the refreshed session', async () => {
    document.cookie = 'acom_csrf=csrf-token; path=/';
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(200, {
      data: {
        user_id: 'local-user',
        login: 'ivanov',
        role_id: 6,
        role: 'economist',
        status: 'active',
      },
    }));

    await expect(refreshWebSession()).resolves.toMatchObject({
      kind: 'success',
      session: { data: { login: 'ivanov' } },
    });
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/auth/refresh',
      expect.objectContaining({
        credentials: 'include',
        headers: expect.objectContaining({ get: expect.any(Function) }),
      })
    );
    const [, requestInit] = fetchMock.mock.calls[0];
    expect(new Headers(requestInit?.headers).get('X-CSRF-Token')).toBe('csrf-token');
  });

  it('classifies a 401 response as terminal without a recursive refresh', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(401));

    await expect(refreshWebSession()).resolves.toEqual({ kind: 'terminal' });
  });

  it.each([502, 503, 504])('classifies HTTP %s as unavailable', async (status) => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(jsonResponse(status, {
      detail: 'Сервис авторизации временно недоступен.',
      reason_code: 'AUTH_SERVICE_UNAVAILABLE',
    }));

    await expect(refreshWebSession()).resolves.toEqual({ kind: 'unavailable' });
  });

  it('classifies a network failure as unavailable', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('network down'));

    await expect(refreshWebSession()).resolves.toEqual({ kind: 'unavailable' });
  });

  it('logs out through the Acom BFF endpoint only', async () => {
    document.cookie = 'acom_csrf=csrf-token; path=/';
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(null, { status: 204 }));

    await expect(logoutWebSession()).resolves.toBeUndefined();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/auth/logout',
      expect.objectContaining({ credentials: 'include', method: 'POST' }),
    );
    const [, requestInit] = fetchMock.mock.calls[0];
    expect(new Headers(requestInit?.headers).get('X-CSRF-Token')).toBe('csrf-token');
  });

  it('clears the IAM UI cookie through the path-matching BFF endpoint', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(null, { status: 204 }));

    await expect(clearIamBrowserSession()).resolves.toBeUndefined();

    expect(fetchMock).toHaveBeenCalledWith(
      '/iam/acom/logout',
      expect.objectContaining({ credentials: 'include', method: 'POST' }),
    );
  });
});
