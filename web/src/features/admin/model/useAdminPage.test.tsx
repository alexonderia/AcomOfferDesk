import { act, renderHook, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { PropsWithChildren } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ROLE } from '@shared/constants/roles';
import type { UserListItem } from '@entities/user';
import { normalizeUserActions } from '@shared/api/mappers';
import { mapUserListItemToContractorListItem } from '@features/contractors/lib/mapUserListItemToContractorListItem';
import { useAdminPage } from './useAdminPage';

const useAuthMock = vi.fn();
const getUsersMock = vi.fn();
const listContractorsMock = vi.fn();
const registerUserMock = vi.fn();
const createManualContractorMock = vi.fn();
const getUnitsTreeMock = vi.fn();
const showErrorToastMock = vi.fn();
const showSuccessToastMock = vi.fn();
const showSystemToastMock = vi.fn();

vi.mock('@app/providers/AuthProvider', () => ({
  useAuth: () => useAuthMock(),
}));

vi.mock('@shared/api/users/getUsers', () => ({
  getUsers: (...args: unknown[]) => getUsersMock(...args),
}));

vi.mock('@shared/api/contractors/listContractors', () => ({
  listContractors: (...args: unknown[]) => listContractorsMock(...args),
}));

vi.mock('@shared/api/auth/registerUser', () => ({
  registerUser: (...args: unknown[]) => registerUserMock(...args),
}));

vi.mock('@shared/api/users/createManualContractor', () => ({
  createManualContractor: (...args: unknown[]) => createManualContractorMock(...args),
}));

vi.mock('@shared/api/units', () => ({
  getUnitsTree: (...args: unknown[]) => getUnitsTreeMock(...args),
}));

vi.mock('@shared/ui/toasts', () => ({
  useSystemToasts: () => ({
    showErrorToast: showErrorToastMock,
    showSuccessToast: showSuccessToastMock,
    showSystemToast: showSystemToastMock,
  }),
}));

const baseSession = {
  roleId: ROLE.SUPERADMIN,
  permissions: [
    'contractors.read',
    'users.create',
    'contractors.manual.create',
    'users.role.update_any',
    'users.status.update',
    'units.read',
    'units.members.manage',
  ],
};

const wrapper = ({ children }: PropsWithChildren) => (
  <MemoryRouter
    initialEntries={['/admin?users_tab=contractors']}
    future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
  >
    {children}
  </MemoryRouter>
);

const buildUser = (userId: string, roleId: number, fullName: string): UserListItem => ({
  user_id: userId, role_id: roleId, full_name: fullName, id_parent: null, status: 'active',
  phone: null, mail: null, company_name: null, inn: null, company_phone: null, company_mail: null,
  address: null, note: null, units_count: 0, managers_count: 0, subordinates_count: 0,
  actions: normalizeUserActions(),
});

describe('useAdminPage', () => {
  beforeEach(() => {
    useAuthMock.mockReset();
    getUsersMock.mockReset();
    listContractorsMock.mockReset();
    registerUserMock.mockReset();
    createManualContractorMock.mockReset();
    getUnitsTreeMock.mockReset();
    showErrorToastMock.mockReset();
    showSuccessToastMock.mockReset();
    showSystemToastMock.mockReset();

    useAuthMock.mockReturnValue({ session: baseSession });
    getUsersMock.mockResolvedValue({ items: [] });
    listContractorsMock.mockResolvedValue([]);
    getUnitsTreeMock.mockResolvedValue([
      {
        unit_id: 1,
        name: 'АО',
        id_parent: null,
        is_active: true,
        members: [],
        children: [
          {
            unit_id: 2,
            name: 'Модуль 1',
            id_parent: 1,
            is_active: true,
            members: [],
            children: [],
            actions: {
              canCreateChild: false,
              canUpdate: false,
              canDelete: false,
              canManageMembers: false,
            },
          },
        ],
        actions: {
          canCreateChild: false,
          canUpdate: false,
          canDelete: false,
          canManageMembers: false,
        },
      },
    ]);
  });

  it('loads contractors via users api when contractors.read is missing', async () => {
    useAuthMock.mockReturnValue({
      session: {
        roleId: ROLE.ADMIN,
        permissions: ['users.read', 'contractors.manual.create', 'contractors.manual.manage'],
      },
    });

    const { result } = renderHook(() => useAdminPage(), { wrapper });

    await waitFor(() => expect(result.current.activeTab).toBe('contractors'));
    await waitFor(() => expect(getUsersMock).toHaveBeenCalled());
    expect(listContractorsMock).not.toHaveBeenCalled();
  });

  it('loads contractors via contractors api on contractors tab', async () => {
    const { result } = renderHook(() => useAdminPage(), { wrapper });

    await waitFor(() => expect(result.current.activeTab).toBe('contractors'));
    await waitFor(() => expect(listContractorsMock).toHaveBeenCalled());
    expect(getUsersMock).not.toHaveBeenCalled();
  });

  it('finds employees of different roles from the contractors tab and filters without refetching', async () => {
    const employees = [
      buildUser('admin-1', ROLE.ADMIN, 'Иванов Иван'),
      buildUser('operator-1', ROLE.OPERATOR, 'Иванов Пётр'),
      buildUser('economist-1', ROLE.ECONOMIST, 'Сидоров Олег'),
    ];
    getUsersMock.mockResolvedValue({ items: [...employees, buildUser('contractor-1', ROLE.CONTRACTOR, 'Иванов')] });
    const { result } = renderHook(useAdminPage, { wrapper });
    await waitFor(() => expect(result.current.isLoadingUsers).toBe(false));

    act(() => result.current.setSearchQuery('  ИВАНОВ  '));
    await waitFor(() => expect(result.current.users.map((user) => user.user_id)).toEqual(['admin-1', 'operator-1']));
    expect(getUsersMock).toHaveBeenCalledWith();
    expect(result.current.activeTab).toBe('contractors');
    const requestCount = getUsersMock.mock.calls.length;

    act(() => result.current.setSearchQuery('operator-1'));
    expect(result.current.users).toEqual([employees[1]]);
    expect(getUsersMock).toHaveBeenCalledTimes(requestCount);

    act(() => result.current.setSearchQuery('несуществующий'));
    expect(result.current.users).toEqual([]);
    expect(result.current.contractors).toEqual([]);

    act(() => result.current.setSearchQuery('   '));
    await waitFor(() => expect(result.current.isLoadingUsers).toBe(false));
    expect(result.current.isGlobalSearch).toBe(false);
    expect(result.current.activeTab).toBe('contractors');
    expect(result.current.users).toEqual([]);
  });

  it('finds contractors by company details while an employee category is selected', async () => {
    const contractor = mapUserListItemToContractorListItem({
      ...buildUser('company-1', ROLE.CONTRACTOR, 'Контактное лицо'),
      company_name: 'ООО Бетон', inn: '1234567890', company_mail: 'office@example.test',
    });
    listContractorsMock.mockResolvedValue([contractor]);
    const { result } = renderHook(useAdminPage, { wrapper });
    act(() => result.current.handleTabChange('operators'));
    await waitFor(() => expect(result.current.isLoadingUsers).toBe(false));

    act(() => result.current.setSearchQuery('бетон'));
    await waitFor(() => expect(result.current.contractors).toEqual([contractor]));
    expect(result.current.activeTab).toBe('operators');
    act(() => result.current.setSearchQuery('1234567890'));
    expect(result.current.contractors).toEqual([contractor]);
    act(() => result.current.setSearchQuery('OFFICE@EXAMPLE.TEST'));
    expect(result.current.contractors).toEqual([contractor]);
  });

  it('uses the users API fallback without contractors.read during global search', async () => {
    useAuthMock.mockReturnValue({ session: { roleId: ROLE.ADMIN, permissions: ['users.read'] } });
    const employee = buildUser('operator-1', ROLE.OPERATOR, 'Иванов');
    const contractor = { ...buildUser('company-1', ROLE.CONTRACTOR, 'Иванов'), inn: '1234567890' };
    getUsersMock.mockImplementation(async (roleId?: number) => ({ items: roleId === ROLE.CONTRACTOR ? [contractor] : [employee] }));
    const { result } = renderHook(useAdminPage, { wrapper });
    await waitFor(() => expect(result.current.isLoadingUsers).toBe(false));
    act(() => result.current.setSearchQuery('Иванов'));
    await waitFor(() => expect(result.current.users).toEqual([employee]));
    expect(result.current.contractors.map((item) => item.userId)).toEqual(['company-1']);
    expect(listContractorsMock).not.toHaveBeenCalled();
  });

  it('keeps global search in the server staff scope for a lead economist', async () => {
    useAuthMock.mockReturnValue({ session: { roleId: ROLE.LEAD_ECONOMIST, permissions: ['users.read'] } });
    const employee = buildUser('operator-visible', ROLE.OPERATOR, 'Иванов');
    getUsersMock.mockResolvedValue({ items: [employee] });
    const { result } = renderHook(useAdminPage, { wrapper });
    await waitFor(() => expect(result.current.isLoadingUsers).toBe(false));
    getUsersMock.mockClear();
    act(() => result.current.setSearchQuery('Иванов'));
    await waitFor(() => expect(result.current.isLoadingUsers).toBe(false));
    expect(getUsersMock).toHaveBeenCalledExactlyOnceWith();
    expect(listContractorsMock).not.toHaveBeenCalled();
    expect(result.current.users).toEqual([employee]);
    expect(result.current.contractors).toEqual([]);
  });

  it('ignores a late global search response after the query is cleared', async () => {
    const { result } = renderHook(useAdminPage, { wrapper });
    await waitFor(() => expect(result.current.isLoadingUsers).toBe(false));
    let resolveSearch!: (value: { items: UserListItem[] }) => void;
    getUsersMock.mockReturnValueOnce(new Promise<{ items: UserListItem[] }>((resolve) => { resolveSearch = resolve; }));
    act(() => result.current.setSearchQuery('Иванов'));
    await waitFor(() => expect(getUsersMock).toHaveBeenCalled());
    act(() => result.current.setSearchQuery(''));
    await waitFor(() => expect(result.current.isLoadingUsers).toBe(false));
    await act(async () => resolveSearch({ items: [buildUser('late', ROLE.OPERATOR, 'Иванов')] }));
    expect(result.current.users).toEqual([]);
    expect(result.current.isGlobalSearch).toBe(false);
  });

  it('clears stale results and reports a failed global search', async () => {
    const { result } = renderHook(useAdminPage, { wrapper });
    await waitFor(() => expect(result.current.isLoadingUsers).toBe(false));
    getUsersMock.mockRejectedValueOnce(new Error('Не удалось загрузить пользователей'));
    act(() => result.current.setSearchQuery('Иванов'));
    await waitFor(() => expect(result.current.usersError).toBe('Не удалось загрузить пользователей'));
    expect(result.current.users).toEqual([]);
    expect(result.current.contractors).toEqual([]);
    expect(result.current.isLoadingUsers).toBe(false);
  });

  it('opens the create dialog with the security officer role on the security tab for superadmin', async () => {
    const { result } = renderHook(() => useAdminPage(), { wrapper });

    await waitFor(() => expect(result.current.activeTab).toBe('contractors'));
    expect(result.current.form.getValues('role_id')).toBe(ROLE.CONTRACTOR);

    act(() => {
      result.current.handleTabChange('security_officers');
    });

    await waitFor(() => expect(result.current.activeTab).toBe('security_officers'));
    await waitFor(() => expect(result.current.roleOptions[0]?.id).toBe(ROLE.SECURITY_OFFICER));

    act(() => {
      result.current.openCreateDialog();
    });

    expect(result.current.form.getValues('role_id')).toBe(ROLE.SECURITY_OFFICER);
    expect(result.current.isContractorRole).toBe(false);
  });

  it('shows all role tabs for admin', async () => {
    useAuthMock.mockReturnValue({
      session: {
        roleId: ROLE.ADMIN,
        permissions: ['users.read', 'users.create', 'users.role.update_any', 'users.status.update'],
      },
    });

    const { result } = renderHook(() => useAdminPage(), { wrapper });

    await waitFor(() => expect(result.current.activeTab).toBe('contractors'));
    expect(result.current.userTabs.map((tab) => tab.value)).toEqual([
      'contractors',
      'admins',
      'security_officers',
      'economists',
      'lead_economists',
      'project_managers',
      'operators',
    ]);
  });

  it('loads unit options for lead economist without units.members.manage', async () => {
    useAuthMock.mockReturnValue({
      session: {
        roleId: ROLE.LEAD_ECONOMIST,
        permissions: ['users.create', 'users.read', 'units.read'],
      },
    });

    const { result } = renderHook(() => useAdminPage(), { wrapper });

    await waitFor(() => expect(result.current.activeTab).toBe('economists'));

    act(() => {
      result.current.openCreateDialog();
    });

    await waitFor(() => expect(getUnitsTreeMock).toHaveBeenCalled());
    await waitFor(() => expect(result.current.unitOptions).toEqual([
      { unitId: 1, label: 'АО' },
      { unitId: 2, label: 'АО / Модуль 1' },
    ]));
    expect(result.current.canShowUnitOnCreate).toBe(true);
    expect(result.current.canAssignUnitOnCreate).toBe(false);
    expect(result.current.form.getValues('unit_id')).toBe(2);
  });

  it('passes selected unit when creating an employee', async () => {
    registerUserMock.mockResolvedValue({
      data: {
        user_id: 'eco-new',
        role_id: ROLE.ECONOMIST,
        status: 'active',
      },
    });

    const { result } = renderHook(() => useAdminPage(), { wrapper });

    await waitFor(() => expect(result.current.activeTab).toBe('contractors'));

    act(() => {
      result.current.handleTabChange('economists');
    });

    await waitFor(() => expect(result.current.activeTab).toBe('economists'));

    act(() => {
      result.current.openCreateDialog();
    });

    await waitFor(() => expect(getUnitsTreeMock).toHaveBeenCalled());
    await waitFor(() => expect(result.current.unitOptions).toEqual([
      { unitId: 1, label: 'АО' },
      { unitId: 2, label: 'АО / Модуль 1' },
    ]));

    act(() => {
      result.current.form.setValue('role_id', ROLE.ECONOMIST);
      result.current.form.setValue('login', 'eco-new');
      result.current.form.setValue('mail', 'eco-new@example.com');
      result.current.form.setValue('unit_id', 2);
    });

    await act(async () => {
      await result.current.onSubmit(result.current.form.getValues());
    });

    expect(registerUserMock).toHaveBeenCalledWith({
      login: 'eco-new',
      role_id: ROLE.ECONOMIST,
      mail: 'eco-new@example.com',
      full_name: undefined,
      phone: undefined,
      unit_id: 2,
    });
  });

  it('does not offer leading economist or operator creation to an administrator', async () => {
    useAuthMock.mockReturnValue({ session: { ...baseSession, roleId: ROLE.ADMIN } });
    const { result } = renderHook(useAdminPage, { wrapper });
    act(() => result.current.handleTabChange('lead_economists'));
    await waitFor(() => expect(result.current.activeTab).toBe('lead_economists'));
    expect(result.current.canOpenCreateDialog).toBe(false);
    act(() => result.current.handleTabChange('operators'));
    await waitFor(() => expect(result.current.roleOptions).toEqual([]));
    expect(result.current.canOpenCreateDialog).toBe(false);
    expect(result.current.roleUpdateOptions).toEqual([ROLE.ECONOMIST]);
  });

  it.each([ROLE.ADMIN, ROLE.CONTRACTOR, ROLE.SECURITY_OFFICER, ROLE.PROJECT_MANAGER, ROLE.LEAD_ECONOMIST, ROLE.ECONOMIST, ROLE.OPERATOR])('does not offer operator assignment for role %s even with both role permissions', async (roleId) => {
    useAuthMock.mockReturnValue({ session: { ...baseSession, roleId, permissions: [...baseSession.permissions, 'users.role.update_economy'] } });
    const { result } = renderHook(useAdminPage, { wrapper });
    await waitFor(() => expect(result.current.isLoadingUsers).toBe(false));
    expect(result.current.roleOptions.map((role) => role.id)).not.toContain(ROLE.OPERATOR);
    expect(result.current.roleUpdateOptions).not.toContain(ROLE.OPERATOR);
  });

  it('allows superadmin to create and assign operator', async () => {
    const { result } = renderHook(useAdminPage, { wrapper });
    act(() => result.current.handleTabChange('operators'));
    await waitFor(() => expect(result.current.activeTab).toBe('operators'));
    expect(result.current.roleOptions[0]).toEqual({ id: ROLE.OPERATOR, label: 'Оператор' });
    expect(result.current.roleUpdateOptions).toContain(ROLE.OPERATOR);
    act(() => result.current.openCreateDialog());
    expect(result.current.form.getValues('role_id')).toBe(ROLE.OPERATOR);
  });

  it('closes creation and navigates to the actual created role for superadmin', async () => {
    registerUserMock.mockResolvedValue({ data: { user_id: 'new-economist', role_id: ROLE.ECONOMIST, status: 'active', visible_to_creator: true } });
    const { result } = renderHook(useAdminPage, { wrapper });
    act(() => result.current.handleTabChange('lead_economists'));
    await waitFor(() => expect(result.current.activeTab).toBe('lead_economists'));
    act(() => result.current.openCreateDialog());
    await act(async () => {
      await result.current.onSubmit({ role_id: ROLE.ECONOMIST, login: 'new-economist', mail: 'new@example.com' });
    });
    await waitFor(() => expect(result.current.activeTab).toBe('economists'));
    expect(result.current.isDialogOpen).toBe(false);
    expect(showSuccessToastMock).toHaveBeenCalledExactlyOnceWith('Сотрудник new-economist создан. Роль: Экономист.');
    expect(showSystemToastMock).not.toHaveBeenCalled();
    expect(getUsersMock).toHaveBeenLastCalledWith(ROLE.ECONOMIST);
  });

  it('explains that an unassigned new employee is outside the creator visibility', async () => {
    useAuthMock.mockReturnValue({ session: { ...baseSession, roleId: ROLE.ADMIN } });
    registerUserMock.mockResolvedValue({ data: { user_id: 'unassigned', role_id: ROLE.ECONOMIST, status: 'active', visible_to_creator: false } });
    const { result } = renderHook(useAdminPage, { wrapper });
    act(() => result.current.handleTabChange('economists'));
    await waitFor(() => expect(result.current.activeTab).toBe('economists'));
    act(() => result.current.openCreateDialog());
    await act(async () => {
      await result.current.onSubmit({ role_id: ROLE.ECONOMIST, login: 'unassigned', mail: 'new@example.com' });
    });
    expect(showSystemToastMock).toHaveBeenCalledExactlyOnceWith({
      severity: 'warning',
      message: 'Сотрудник unassigned создан. Роль: Экономист. Он не входит в вашу область видимости. Обратитесь к суперадминистратору для назначения сотрудника в доступное вам подразделение.',
    });
    expect(showSuccessToastMock).not.toHaveBeenCalled();
    expect(result.current.isDialogOpen).toBe(false);
  });
});
