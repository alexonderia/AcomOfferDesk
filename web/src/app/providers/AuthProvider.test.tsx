import { act, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { AuthProvider, useAuth } from '@app/providers/AuthProvider';
import { setAuthRuntime } from '@shared/api/client';

const authApi = vi.hoisted(() => ({
  getWebSession: vi.fn(),
  issueCsrfToken: vi.fn(),
  logoutWebSession: vi.fn(),
  refreshWebSession: vi.fn(),
  clearIamBrowserSession: vi.fn(),
}));

vi.mock('@shared/api/auth/loginWebUser', () => authApi);
vi.mock('@shared/api/client', () => ({ setAuthRuntime: vi.fn() }));

const sessionResponse = {
  data: {
    user_id: 'local-user',
    login: 'ivanov',
    role_id: 6,
    role: 'economist',
    status: 'active',
    auth_provider: 'iam',
    business_access: true,
    onboarding_state: null,
    permissions: ['requests.view'],
  },
};

const AuthSnapshot = () => {
  const { status, isAuthenticated, session } = useAuth();
  return (
    <div>
      <div data-testid="status">{status}</div>
      <div data-testid="authenticated">{String(isAuthenticated)}</div>
      <div data-testid="session">{session?.login ?? 'none'}</div>
    </div>
  );
};

let refreshFromContext: ReturnType<typeof useAuth>['refresh'] | null = null;
let logoutFromContext: ReturnType<typeof useAuth>['logout'] | null = null;

const RefreshCapture = () => {
  refreshFromContext = useAuth().refresh;
  logoutFromContext = useAuth().logout;
  return null;
};

describe('AuthProvider IAM BFF session', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    authApi.issueCsrfToken.mockResolvedValue(undefined);
    refreshFromContext = null;
    logoutFromContext = null;
  });

  it('restores an authenticated session from HttpOnly cookies', async () => {
    authApi.getWebSession.mockResolvedValue(sessionResponse);

    render(<AuthProvider><AuthSnapshot /></AuthProvider>);

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('authenticated'));
    expect(screen.getByTestId('authenticated')).toHaveTextContent('true');
    expect(screen.getByTestId('session')).toHaveTextContent('ivanov');
    expect(setAuthRuntime).toHaveBeenCalled();
  });

  it('restores the session after bootstrap finds an expired access cookie', async () => {
    authApi.getWebSession.mockRejectedValue(new Error('expired access cookie'));
    authApi.refreshWebSession.mockResolvedValue({ kind: 'success', session: sessionResponse });

    render(<AuthProvider><AuthSnapshot /></AuthProvider>);

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('authenticated'));
    expect(screen.getByTestId('session')).toHaveTextContent('ivanov');
    expect(authApi.refreshWebSession).toHaveBeenCalledTimes(1);
  });

  it('shows controlled unavailability when session and refresh cannot reach IAM', async () => {
    authApi.getWebSession.mockRejectedValue(new Error('Сеть недоступна'));
    authApi.refreshWebSession.mockResolvedValue({ kind: 'unavailable' });

    render(<AuthProvider><AuthSnapshot /></AuthProvider>);

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('unavailable'));
    expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
    expect(screen.getByTestId('session')).toHaveTextContent('none');
  });

  it('uses one refresh operation for concurrent REST and WS consumers and releases the lock', async () => {
    authApi.getWebSession.mockResolvedValue(sessionResponse);
    let resolveRefresh: (value: unknown) => void = () => undefined;
    authApi.refreshWebSession.mockImplementation(() => new Promise((resolve) => {
      resolveRefresh = resolve;
    }));

    render(<AuthProvider><RefreshCapture /><AuthSnapshot /></AuthProvider>);
    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('authenticated'));
    expect(refreshFromContext).not.toBeNull();

    const refresh = refreshFromContext!;
    const first = refresh('http_401');
    const second = refresh('ws_4401');
    const third = refresh('http_401');
    await waitFor(() => expect(authApi.refreshWebSession).toHaveBeenCalledTimes(1));
    resolveRefresh({ kind: 'success', session: sessionResponse });

    await expect(Promise.all([first, second, third])).resolves.toEqual([
      { kind: 'success' },
      { kind: 'success' },
      { kind: 'success' },
    ]);

    authApi.refreshWebSession.mockResolvedValue({ kind: 'success', session: sessionResponse });
    await refresh('http_401');
    expect(authApi.refreshWebSession).toHaveBeenCalledTimes(2);
  });

  it('keeps the previous session and enters unavailable state for a transient refresh failure', async () => {
    authApi.getWebSession.mockResolvedValue(sessionResponse);
    authApi.refreshWebSession.mockResolvedValue({ kind: 'unavailable' });

    render(<AuthProvider><RefreshCapture /><AuthSnapshot /></AuthProvider>);
    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('authenticated'));

    await act(async () => {
      await expect(refreshFromContext!('http_401')).resolves.toEqual({ kind: 'unavailable' });
    });

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('unavailable'));
    expect(screen.getByTestId('session')).toHaveTextContent('ivanov');
  });

  it('clears the session for a terminal refresh failure', async () => {
    authApi.getWebSession.mockResolvedValue(sessionResponse);
    authApi.refreshWebSession.mockResolvedValue({ kind: 'terminal' });

    render(<AuthProvider><RefreshCapture /><AuthSnapshot /></AuthProvider>);
    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('authenticated'));

    await act(async () => {
      await expect(refreshFromContext!('http_401')).resolves.toEqual({ kind: 'terminal' });
    });

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('unauthenticated'));
    expect(screen.getByTestId('session')).toHaveTextContent('none');
  });

  it('exposes a new session revision after refresh for delayed REST responses', async () => {
    authApi.getWebSession.mockResolvedValue(sessionResponse);
    authApi.refreshWebSession.mockResolvedValue({ kind: 'success', session: sessionResponse });
    render(<AuthProvider><RefreshCapture /><AuthSnapshot /></AuthProvider>);
    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('authenticated'));
    const runtime = vi.mocked(setAuthRuntime).mock.calls.at(-1)![0]!;
    const previousRevision = runtime.getSessionRevision();

    await act(async () => { await refreshFromContext!('http_401'); });

    expect(runtime.getSessionRevision()).toBeGreaterThan(previousRevision);
  });

  it('waits for cookie rotation before logout and never restores the session during logout', async () => {
    authApi.getWebSession.mockResolvedValue(sessionResponse);
    let finishRefresh!: (value: unknown) => void;
    authApi.refreshWebSession.mockImplementation(() => new Promise((resolve) => { finishRefresh = resolve; }));
    // Keep navigation pending; only the ordering of refresh, state clearing and revocation matters here.
    authApi.logoutWebSession.mockImplementation(() => new Promise(() => undefined));
    render(<AuthProvider><RefreshCapture /><AuthSnapshot /></AuthProvider>);
    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('authenticated'));
    const refreshing = refreshFromContext!('http_401');
    await waitFor(() => expect(authApi.refreshWebSession).toHaveBeenCalledTimes(1));

    act(() => { logoutFromContext!(); });
    await act(async () => { await Promise.resolve(); });
    expect(authApi.logoutWebSession).not.toHaveBeenCalled();
    expect(screen.getByTestId('status')).toHaveTextContent('signing_out');
    await act(async () => {
      finishRefresh({ kind: 'success', session: sessionResponse });
      await expect(refreshing).resolves.toEqual({ kind: 'terminal' });
    });

    await waitFor(() => expect(authApi.logoutWebSession).toHaveBeenCalledTimes(1));
    expect(screen.getByTestId('session')).toHaveTextContent('none');
    await expect(refreshFromContext!('http_401')).resolves.toEqual({ kind: 'terminal' });
    expect(authApi.refreshWebSession).toHaveBeenCalledTimes(1);
  });
});
