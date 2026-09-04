import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { AuthPage } from './AuthPage';

const auth = vi.hoisted(() => ({
  beginLogin: vi.fn(),
  status: 'unauthenticated' as 'unauthenticated' | 'unavailable',
}));
const passwordReset = vi.hoisted(() => vi.fn());
const toasts = vi.hoisted(() => ({ showErrorToast: vi.fn(), showSuccessToast: vi.fn() }));

vi.mock('@app/providers/AuthProvider', () => ({ useAuth: () => auth }));
vi.mock('@shared/api/auth', () => ({ requestPasswordReset: passwordReset }));
vi.mock('@shared/ui/toasts', () => ({ useSystemToasts: () => toasts }));

const renderPage = () => render(
  <MemoryRouter initialEntries={['/login?reset=1']}>
    <AuthPage />
  </MemoryRouter>,
);

describe('AuthPage password reset', () => {
  beforeEach(() => {
    auth.status = 'unauthenticated';
    vi.clearAllMocks();
  });

  it('reports a successful reset request through the shared success toast', async () => {
    passwordReset.mockResolvedValue('Если учётная запись существует, инструкция отправлена на подтверждённый email.');
    renderPage();

    fireEvent.change(screen.getByLabelText('Логин или email'), { target: { value: 'superadmin' } });
    fireEvent.click(screen.getByRole('button', { name: 'Отправить инструкцию' }));

    await waitFor(() => expect(toasts.showSuccessToast).toHaveBeenCalledTimes(1));
    expect(toasts.showErrorToast).not.toHaveBeenCalled();
    expect(screen.queryByText('Если учётная запись существует, инструкция отправлена на подтверждённый email.')).toBeNull();
  });

  it('uses the technical page for an unavailable authorization service', async () => {
    auth.status = 'unavailable';
    renderPage();

    expect(screen.getByRole('heading', { name: 'Ведутся технические работы' })).toBeInTheDocument();
  });

  it('starts IAM login immediately unless password recovery was explicitly requested', () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <AuthPage />
      </MemoryRouter>,
    );

    expect(auth.beginLogin).toHaveBeenCalledWith('/');
  });
});
