import { ThemeProvider } from '@mui/material/styles';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { appTheme } from '@shared/theme/appTheme';
import { PasswordChangeForm } from './PasswordChangeForm';

const mocks = vi.hoisted(() => ({ change: vi.fn(), logout: vi.fn(), success: vi.fn() }));
vi.mock('@app/providers/AuthProvider', () => ({ useAuth: () => ({ logout: mocks.logout }) }));
vi.mock('@shared/api/auth/changePassword', () => ({ changePassword: mocks.change }));
vi.mock('@shared/ui/toasts', () => ({ useSystemToasts: () => ({ showSuccessToast: mocks.success }) }));

const fill = () => {
  render(<ThemeProvider theme={appTheme}><PasswordChangeForm /></ThemeProvider>);
  fireEvent.change(screen.getByLabelText(/^Текущий пароль\s*\*?$/), { target: { value: 'old password 123' } });
  fireEvent.change(screen.getByLabelText(/^Новый пароль\s*\*?$/), { target: { value: 'new password 456' } });
  fireEvent.change(screen.getByLabelText(/^Повтор нового пароля\s*\*?$/), { target: { value: 'new password 456' } });
};

describe('self password change', () => {
  beforeEach(() => vi.clearAllMocks());
  it('submits current password and requires a new login after success', async () => {
    mocks.change.mockResolvedValue(undefined);
    fill();
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить пароль' }));
    await waitFor(() => expect(mocks.logout).toHaveBeenCalledOnce());
    expect(mocks.change).toHaveBeenCalledWith({ current_password: 'old password 123', new_password: 'new password 456', password_confirmation: 'new password 456' });
  });
  it('keeps the current session when the old password is rejected', async () => {
    mocks.change.mockRejectedValue(new Error('Текущий пароль указан неверно'));
    fill();
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить пароль' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Текущий пароль указан неверно');
    expect(mocks.logout).not.toHaveBeenCalled();
  });
  it('rejects mismatched confirmation without calling the API', async () => {
    fill();
    fireEvent.change(screen.getByLabelText(/^Повтор нового пароля\s*\*?$/), { target: { value: 'different password 789' } });
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить пароль' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('совпадающий новый пароль');
    expect(mocks.change).not.toHaveBeenCalled();
  });
  it('clears password drafts without opening another dialog', () => {
    fill();
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Очистить' }));
    expect(screen.getByLabelText(/^Текущий пароль\s*\*?$/)).toHaveValue('');
    expect(screen.getByLabelText(/^Новый пароль\s*\*?$/)).toHaveValue('');
    expect(screen.getByLabelText(/^Повтор нового пароля\s*\*?$/)).toHaveValue('');
    expect(mocks.change).not.toHaveBeenCalled();
  });
});
