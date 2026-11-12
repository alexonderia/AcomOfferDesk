import { ThemeProvider } from '@mui/material/styles';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { UserListItem } from '@entities/user';
import { normalizeUserActions } from '@shared/api/mappers';
import { appTheme } from '@shared/theme/appTheme';
import { ROLE } from '@shared/constants/roles';
import { updateUserRole } from '@shared/api/users/updateUserRole';
import { UsersTable } from './UsersTable';

const useAuthMock = vi.fn();

vi.mock('@app/providers/AuthProvider', () => ({
  useAuth: () => useAuthMock(),
}));
vi.mock('@shared/api/users/updateUserRole', () => ({ updateUserRole: vi.fn().mockResolvedValue({}) }));
vi.mock('@shared/ui/toasts', () => ({
  useSystemToasts: () => ({ showSystemToast: vi.fn(), showErrorToast: vi.fn() }),
}));
vi.mock('@shared/api/users/getUserHierarchy', () => ({ getUserHierarchy: vi.fn().mockResolvedValue(null) }));
vi.mock('@shared/api/users/getUserHierarchyUnitsTree', () => ({ getUserHierarchyUnitsTree: vi.fn().mockResolvedValue([]) }));
vi.mock('@shared/api/users/getDepartmentDelegations', () => ({
  getDepartmentDelegations: vi.fn().mockResolvedValue({ userId: 'admin-1', canManage: true, accesses: [] }),
  updateDepartmentDelegations: vi.fn(),
}));

describe('UsersTable employee card', () => {
  beforeEach(() => {
    useAuthMock.mockReturnValue({ session: { roleId: ROLE.SUPERADMIN, permissions: ['users.read'] } });
    vi.mocked(updateUserRole).mockClear();
  });

  it('keeps the shared card, server counts and existing management actions when opened from the table', async () => {
    const employee: UserListItem = {
      user_id: 'admin-1', role_id: 2, id_parent: null, status: 'active',
      full_name: 'Иванов Иван Иванович', phone: '+79991234567', mail: 'ivan@example.test',
      company_name: null, inn: null, company_phone: null, company_mail: null, address: null, note: null,
      units_count: 2, managers_count: 3, subordinates_count: 4, actions: normalizeUserActions({ can_reset_password: true }),
    };
    render(<ThemeProvider theme={appTheme}>
      <UsersTable users={[employee]} emptyMessage="Нет сотрудников" getRoleLabel={() => 'Администратор'}
        isContractorsTab={false} canViewRoleIds={false} canUpdateStatus={false} canUpdateRole={false}
        allowedRoleOptions={[]} onStatusUpdated={async () => {}} />
    </ThemeProvider>);
    fireEvent.click(screen.getByText(employee.full_name!));

    const card = await screen.findByRole('dialog', { name: 'Карточка сотрудника' });
    expect(within(card).getByText('ivan@example.test')).toBeVisible();
    expect(within(card).getByText('Иерархия по объединениям')).toBeVisible();
    for (const count of ['2', '3', '4']) expect(within(card).getByText(count)).toBeVisible();
    expect(within(card).getByRole('button', { name: 'Сбросить пароль' })).toBeVisible();
    expect(await within(card).findByText('Дополнительные доступы к подразделению')).toBeVisible();
    fireEvent.click(within(card).getByRole('button', { name: 'Закрыть' }));
    expect(screen.getByText(employee.full_name!)).toBeVisible();
  });

  it('allows changing an existing operator to economist while operator is disabled in the role menu', async () => {
    useAuthMock.mockReturnValue({ session: { roleId: ROLE.ADMIN, permissions: ['users.read', 'users.role.update_any'] } });
    const operator: UserListItem = {
      user_id: 'operator-1', role_id: ROLE.OPERATOR, id_parent: null, status: 'active',
      full_name: 'Оператор Иванов', phone: null, mail: null,
      company_name: null, inn: null, company_phone: null, company_mail: null, address: null, note: null,
      units_count: 1, managers_count: 0, subordinates_count: 0,
      actions: { ...normalizeUserActions(), update_role: true },
    };
    const onStatusUpdated = vi.fn().mockResolvedValue(undefined);
    render(<ThemeProvider theme={appTheme}>
      <UsersTable users={[operator]} emptyMessage="Нет сотрудников"
        getRoleLabel={(roleId) => roleId === ROLE.OPERATOR ? 'Оператор' : 'Экономист'}
        isContractorsTab={false} canViewRoleIds={false} canUpdateStatus={false} canUpdateRole
        allowedRoleOptions={[ROLE.ECONOMIST]} onStatusUpdated={onStatusUpdated} />
    </ThemeProvider>);

    const roleSelect = screen.getByRole('combobox', { name: 'Роль пользователя operator-1' });
    fireEvent.keyDown(roleSelect, { key: 'ArrowDown' });
    const menu = await screen.findByRole('listbox');
    expect(within(menu).getByRole('option', { name: 'Оператор' })).toHaveAttribute('aria-disabled', 'true');
    fireEvent.click(within(menu).getByRole('option', { name: 'Экономист' }));

    await waitFor(() => expect(updateUserRole).toHaveBeenCalledWith('operator-1', { role_id: ROLE.ECONOMIST }));
    await waitFor(() => expect(onStatusUpdated).toHaveBeenCalled());
  });
});
