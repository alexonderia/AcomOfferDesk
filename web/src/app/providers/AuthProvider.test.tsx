import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { AuthProvider, useAuth } from '@app/providers/AuthProvider';
import { setAuthRuntime, setAuthToken } from '@shared/api/client';

vi.mock('@shared/api/client', () => ({
  setAuthRuntime: vi.fn(),
  setAuthToken: vi.fn()
}));

const AuthSnapshot = () => {
  const { status, isAuthenticated, session, refresh, beginLogin } = useAuth();
  return (
    <div>
      <div data-testid="status">{status}</div>
      <div data-testid="authenticated">{String(isAuthenticated)}</div>
      <div data-testid="session">{session ? 'present' : 'none'}</div>
      <button type="button" onClick={() => void refresh('bootstrap')}>refresh</button>
      <button type="button" onClick={() => beginLogin('/requests/42')}>login</button>
    </div>
  );
};

const renderProvider = () => render(
  <MemoryRouter initialEntries={['/requests']}>
    <Routes>
      <Route path="/login" element={<div>login-page</div>} />
      <Route path="*" element={<AuthProvider><AuthSnapshot /></AuthProvider>} />
    </Routes>
  </MemoryRouter>
);

describe('AuthProvider unavailable mode', () => {
  beforeEach(() => vi.clearAllMocks());

  it('starts without a session and never installs a token', () => {
    renderProvider();

    expect(screen.getByTestId('status')).toHaveTextContent('unavailable');
    expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
    expect(screen.getByTestId('session')).toHaveTextContent('none');
    expect(setAuthToken).toHaveBeenCalledWith(null);
    expect(setAuthRuntime).toHaveBeenCalled();
  });

  it('does not attempt a provider refresh', async () => {
    renderProvider();

    fireEvent.click(screen.getByText('refresh'));

    expect(screen.getByTestId('status')).toHaveTextContent('unavailable');
    const runtime = vi.mocked(setAuthRuntime).mock.calls[0][0];
    await expect(runtime?.refresh('http_401')).resolves.toBe(false);
    expect(runtime?.canAttemptSilentRefresh('http_401')).toBe(false);
  });

  it('keeps login inside the application and never redirects to OIDC', () => {
    renderProvider();

    fireEvent.click(screen.getByText('login'));

    expect(screen.getByText('login-page')).toBeInTheDocument();
  });
});
