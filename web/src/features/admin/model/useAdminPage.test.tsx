import { act, renderHook, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { PropsWithChildren } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ROLE } from '@shared/constants/roles';
import { useAdminPage } from './useAdminPage';

const useAuthMock = vi.fn();
const getUsersMock = vi.fn();
const listContractorsMock = vi.fn();
const registerUserMock = vi.fn();
const createManualContractorMock = vi.fn();
const getUnitsTreeMock = vi.fn();
const showErrorToastMock = vi.fn();
const showSuccessToastMock = vi.fn();

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
});
