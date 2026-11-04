import { ThemeProvider } from '@mui/material/styles';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ROLE } from '@shared/constants/roles';
import { appTheme } from '@shared/theme/appTheme';
import { UserPasswordResetButton } from './UserPasswordResetButton';

const mocks = vi.hoisted(() => ({ reset: vi.fn(), success: vi.fn(), roleId: 1 }));
vi.mock('@app/providers/AuthProvider', () => ({ useAuth: () => ({ session: { roleId: mocks.roleId } }) }));
vi.mock('@shared/api/users/resetUserPassword', () => ({ resetUserPassword: mocks.reset }));
vi.mock('@shared/ui/toasts', () => ({ useSystemToasts: () => ({ showSuccessToast: mocks.success }) }));

const mount = (roleId: number = ROLE.ECONOMIST) => render(
  <ThemeProvider theme={appTheme}><UserPasswordResetButton userId="employee" roleId={roleId} /></ThemeProvider>,
);
const open = () => fireEvent.click(screen.getByRole('button', { name: 'Сбросить пароль' }));
const fill = () => {
  fireEvent.change(screen.getByLabelText(/^Новый пароль\s*\*?$/), { target: { value: 'New password 456' } });
  fireEvent.change(screen.getByLabelText(/^Повтор нового пароля\s*\*?$/), { target: { value: 'New password 456' } });
};

describe('administrator password reset', () => {
  beforeEach(() => { vi.clearAllMocks(); mocks.roleId = ROLE.SUPERADMIN; });

  it.each([ROLE.ADMIN, ROLE.CONTRACTOR, ROLE.SECURITY_OFFICER, ROLE.PROJECT_MANAGER, ROLE.LEAD_ECONOMIST, ROLE.ECONOMIST, ROLE.OPERATOR])('hides action for role %s', (roleId) => {
    mocks.roleId = roleId;
    mount();
    expect(screen.queryByRole('button', { name: 'Сбросить пароль' })).not.toBeInTheDocument();
  });

  it('protects every superadmin account', () => {
    mount(ROLE.SUPERADMIN);
    expect(screen.queryByRole('button', { name: 'Сбросить пароль' })).not.toBeInTheDocument();
  });

  it('sets a new password without old password and closes after success', async () => {
    mocks.reset.mockResolvedValue(undefined);
    mount(); open(); fill();
    expect(screen.queryByLabelText(/^Текущий пароль/)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Установить новый пароль' }));
    await waitFor(() => expect(mocks.success).toHaveBeenCalledOnce());
    expect(mocks.reset).toHaveBeenCalledWith('employee', { new_password: 'New password 456', password_confirmation: 'New password 456' });
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
  });

  it('rejects mismatched passwords and allows independent visibility', async () => {
    mount(); open(); fill();
    fireEvent.click(screen.getByRole('button', { name: 'Показать новый пароль' }));
    expect(screen.getByLabelText(/^Новый пароль\s*\*?$/)).toHaveAttribute('type', 'text');
    expect(screen.getByLabelText(/^Повтор нового пароля\s*\*?$/)).toHaveAttribute('type', 'password');
    fireEvent.change(screen.getByLabelText(/^Повтор нового пароля\s*\*?$/), { target: { value: 'Other password 789' } });
    fireEvent.click(screen.getByRole('button', { name: 'Установить новый пароль' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('совпадающий новый пароль');
    expect(mocks.reset).not.toHaveBeenCalled();
  });

  it('clears secrets and visibility when cancelled and reopened', async () => {
    mount(); open(); fill();
    fireEvent.click(screen.getByRole('button', { name: 'Показать новый пароль' }));
    fireEvent.click(screen.getByRole('button', { name: 'Отмена' }));
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    open();
    expect(screen.getByLabelText(/^Новый пароль\s*\*?$/)).toHaveValue('');
    expect(screen.getByLabelText(/^Новый пароль\s*\*?$/)).toHaveAttribute('type', 'password');
    expect(screen.getByLabelText(/^Повтор нового пароля\s*\*?$/)).toHaveValue('');
    expect(mocks.reset).not.toHaveBeenCalled();
  });

  it('shows API failure and keeps form open for correction', async () => {
    mocks.reset.mockRejectedValue(new Error('Сброс запрещён'));
    mount(); open(); fill();
    fireEvent.click(screen.getByRole('button', { name: 'Установить новый пароль' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Сброс запрещён');
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(mocks.success).not.toHaveBeenCalled();
  });
});
