import { ThemeProvider } from '@mui/material/styles';
import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { UserListItem } from '@entities/user';
import { normalizeUserActions } from '@shared/api/mappers';
import { appTheme } from '@shared/theme/appTheme';
import { UsersTable } from './UsersTable';

vi.mock('@app/providers/AuthProvider', () => ({
  useAuth: () => ({ session: { roleId: 1, permissions: ['users.read'] } }),
}));
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
  it('keeps the shared card, server counts and existing management actions when opened from the table', async () => {
    const employee: UserListItem = {
      user_id: 'admin-1', role_id: 2, id_parent: null, status: 'active',
      full_name: 'Иванов Иван Иванович', phone: '+79991234567', mail: 'ivan@example.test',
      company_name: null, inn: null, company_phone: null, company_mail: null, address: null, note: null,
      units_count: 2, managers_count: 3, subordinates_count: 4, actions: normalizeUserActions(),
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
});
