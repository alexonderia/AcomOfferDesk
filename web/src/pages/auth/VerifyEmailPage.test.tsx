import { render, waitFor, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { VerifyEmailPage } from './VerifyEmailPage';

const navigateMock = vi.fn();
const useAuthMock = vi.fn();
const verifyEmailTokenMock = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

vi.mock('@app/providers/AuthProvider', () => ({
  useAuth: () => useAuthMock(),
}));

vi.mock('@shared/api/auth/emailVerification', () => ({
  verifyEmailToken: (token: string) => verifyEmailTokenMock(token),
}));

const baseSession = {
  token: 'token',
  tokenType: 'bearer',
  tokenExpiresAt: 1_700_000_000,
  userId: 'votomeg489',
  login: 'votomeg489',
  roleId: 3,
  role: 'contractor',
  status: 'review',
  authProvider: 'iam',
  businessAccess: false,
  onboardingState: 'review',
  permissions: [] as string[],
  appRoles: ['app.contractor'],
  delegationRoles: [] as string[],
};

const renderPage = (initialEntry = '/verify-email?token=test-token') => render(
  <MemoryRouter initialEntries={[initialEntry]} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
    <VerifyEmailPage />
  </MemoryRouter>
);

describe('VerifyEmailPage', () => {
  beforeEach(() => {
    navigateMock.mockReset();
    useAuthMock.mockReset();
    verifyEmailTokenMock.mockReset();

    useAuthMock.mockReturnValue({
      status: 'authenticated',
      isAuthenticated: true,
      session: baseSession,
    });
  });

  it('returns authenticated onboarding users to account state after email confirmation', async () => {
    verifyEmailTokenMock.mockResolvedValue({ detail: 'Email подтверждён' });

    renderPage();

    await waitFor(() => {
      expect(verifyEmailTokenMock).toHaveBeenCalledWith('test-token');
    });
    await waitFor(() => {
      expect(navigateMock).toHaveBeenCalledWith('/account', { replace: true });
    });
  });

  it('does not redirect anonymous users after email confirmation', async () => {
    useAuthMock.mockReturnValue({
      status: 'anonymous',
      isAuthenticated: false,
      session: null,
    });
    verifyEmailTokenMock.mockResolvedValue({ detail: 'Email подтверждён' });

    renderPage();

    await waitFor(() => {
      expect(verifyEmailTokenMock).toHaveBeenCalledWith('test-token');
    });

    expect(navigateMock).not.toHaveBeenCalled();
  });

  it('asks to verify email after registration submit without consuming a token', async () => {
    useAuthMock.mockReturnValue({
      status: 'anonymous',
      isAuthenticated: false,
      session: null,
    });

    renderPage('/verify-email?next=check_email&invite=invite-token-value-123456');

    expect(await screen.findByText('Подтвердите email')).toBeInTheDocument();
    expect(
      screen.getByText(/Мы отправили письмо на указанный адрес/i),
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Изменить данные' })).toHaveAttribute(
      'href',
      '/register?token=invite-token-value-123456',
    );
    expect(screen.queryByText('Email подтверждён.')).not.toBeInTheDocument();
    expect(verifyEmailTokenMock).not.toHaveBeenCalled();
    expect(navigateMock).not.toHaveBeenCalled();
  });
});
