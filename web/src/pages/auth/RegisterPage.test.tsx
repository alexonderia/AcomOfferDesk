import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { RegisterPage } from './RegisterPage';

const inspectMock = vi.hoisted(() => vi.fn());
const submitMock = vi.hoisted(() => vi.fn());
const navigateMock = vi.hoisted(() => vi.fn());
const toasts = vi.hoisted(() => ({ showErrorToast: vi.fn(), showSuccessToast: vi.fn() }));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});
vi.mock('@shared/api/auth/registration', () => ({
  inspectRegistrationInvitation: inspectMock,
  submitRegistration: submitMock,
}));
vi.mock('@shared/ui/toasts', () => ({ useSystemToasts: () => toasts }));

const renderPage = (entry = '/register?token=invite-token-value-123456') =>
  render(
    <MemoryRouter initialEntries={[entry]}>
      <RegisterPage />
    </MemoryRouter>,
  );

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    inspectMock.mockResolvedValue({ data: { status: 'ok', email: 'invite@example.com' } });
    submitMock.mockResolvedValue({
      data: { user_id: 'contractor1', status: 'review', email: 'invite@example.com' },
      detail: 'Регистрация принята. Подтвердите email и дождитесь проверки.',
    });
  });

  it('prefills invitation email', async () => {
    renderPage();
    expect(await screen.findByDisplayValue('invite@example.com')).toBeInTheDocument();
  });

  it('redirects expired invitations to the status page', async () => {
    inspectMock.mockResolvedValue({ data: { status: 'expired' } });
    renderPage();
    await waitFor(() => {
      expect(navigateMock).toHaveBeenCalledWith(
        '/auth/registration-link-status?reason=expired',
        { replace: true },
      );
    });
  });

  it('opens the check-email page after successful submit', async () => {
    renderPage();
    await screen.findByDisplayValue('invite@example.com');
    fireEvent.change(screen.getByLabelText(/Логин/i), { target: { value: 'contractor1' } });
    // PR #53 (auth→IAM migration): registration form no longer collects a password;
    // credentials are handled by the IAM portal on first login.
    fireEvent.change(screen.getByLabelText(/ФИО/i), { target: { value: 'Иванов Иван' } });
    const phoneInputs = screen.getAllByLabelText(/Телефон/i);
    fireEvent.change(phoneInputs[0], { target: { value: '+7 (900) 111-22-33' } });
    fireEvent.change(screen.getByLabelText(/Компания/i), { target: { value: 'ООО Тест' } });
    fireEvent.change(screen.getByLabelText(/ИНН/i), { target: { value: '1234567890' } });
    fireEvent.change(phoneInputs[1], { target: { value: '+7 (900) 111-22-34' } });
    fireEvent.click(screen.getByRole('button', { name: 'Отправить заявку' }));
    await waitFor(() => {
      expect(submitMock).toHaveBeenCalled();
    });
    expect(navigateMock).toHaveBeenCalledWith(
      `/verify-email?next=check_email&invite=${encodeURIComponent('invite-token-value-123456')}`,
      { replace: true },
    );
  });
});
