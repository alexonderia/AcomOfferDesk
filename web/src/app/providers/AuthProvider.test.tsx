import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { AuthProvider, useAuth } from '@app/providers/AuthProvider';
import { setAuthRuntime } from '@shared/api/client';

const authApi = vi.hoisted(() => ({
  getWebSession: vi.fn(),
  issueCsrfToken: vi.fn(),
  logoutWebSession: vi.fn(),
  refreshWebSession: vi.fn(),
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

describe('AuthProvider IAM BFF session', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    authApi.issueCsrfToken.mockResolvedValue(undefined);
  });

  it('restores an authenticated session from HttpOnly cookies', async () => {
    authApi.getWebSession.mockResolvedValue(sessionResponse);

    render(<AuthProvider><AuthSnapshot /></AuthProvider>);

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('authenticated'));
    expect(screen.getByTestId('authenticated')).toHaveTextContent('true');
    expect(screen.getByTestId('session')).toHaveTextContent('ivanov');
    expect(setAuthRuntime).toHaveBeenCalled();
  });

  it('shows controlled unavailability when session and refresh cannot reach IAM', async () => {
    authApi.getWebSession.mockRejectedValue(new Error('Сеть недоступна'));
    authApi.refreshWebSession.mockRejectedValue(new Error('Сеть недоступна'));

    render(<AuthProvider><AuthSnapshot /></AuthProvider>);

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('unavailable'));
    expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
    expect(screen.getByTestId('session')).toHaveTextContent('none');
  });
});
