import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ROLE } from '@shared/constants/roles';
import { useUnitHierarchyPage } from './useUnitHierarchyPage';

const useAuthMock = vi.fn();
const getUnitsTreeMock = vi.fn();
const getRecommendedUnitsTreeMock = vi.fn();
const getAvailableUsersForUnitMock = vi.fn();
const addUnitMemberMock = vi.fn();
const createUnitMock = vi.fn();
const removeUnitMemberMock = vi.fn();
const updateUnitMock = vi.fn();
const showErrorToastMock = vi.fn();
const showSuccessToastMock = vi.fn();

vi.mock('@app/providers/AuthProvider', () => ({
  useAuth: () => useAuthMock(),
}));

vi.mock('@shared/api/units', () => ({
  getUnitsTree: (...args: unknown[]) => getUnitsTreeMock(...args),
  getRecommendedUnitsTree: (...args: unknown[]) => getRecommendedUnitsTreeMock(...args),
  getAvailableUsersForUnit: (...args: unknown[]) => getAvailableUsersForUnitMock(...args),
  addUnitMember: (...args: unknown[]) => addUnitMemberMock(...args),
  createUnit: (...args: unknown[]) => createUnitMock(...args),
  removeUnitMember: (...args: unknown[]) => removeUnitMemberMock(...args),
  updateUnit: (...args: unknown[]) => updateUnitMock(...args),
}));

vi.mock('@shared/ui/toasts', () => ({
  useSystemToasts: () => ({
    showErrorToast: showErrorToastMock,
    showSuccessToast: showSuccessToastMock,
  }),
}));

const baseSession = {
  roleId: ROLE.SUPERADMIN,
  permissions: ['units.read', 'units.create', 'units.members.manage'],
};

const treeResponse = [
  {
    unit_id: 1,
    name: 'Head Office',
    id_parent: null,
    level: 0,
    is_active: true,
    members: [],
    actions: {
      canCreateChild: true,
      canUpdate: true,
      canDeactivate: true,
      canManageMembers: true,
    },
    children: [],
  },
];

describe('useUnitHierarchyPage', () => {
  beforeEach(() => {
    useAuthMock.mockReset();
    getUnitsTreeMock.mockReset();
    getRecommendedUnitsTreeMock.mockReset();
    getAvailableUsersForUnitMock.mockReset();
    addUnitMemberMock.mockReset();
    createUnitMock.mockReset();
    removeUnitMemberMock.mockReset();
    updateUnitMock.mockReset();
    showErrorToastMock.mockReset();
    showSuccessToastMock.mockReset();

    useAuthMock.mockReturnValue({ session: baseSession });
    getUnitsTreeMock.mockResolvedValue(treeResponse);
    getRecommendedUnitsTreeMock.mockResolvedValue([
      {
        user_id: 'pm-1',
        full_name: 'Manager',
        role_id: ROLE.PROJECT_MANAGER,
        role_name: 'Project Manager',
        status: 'active',
        id_parent_user: null,
        children: [],
      },
    ]);
    getAvailableUsersForUnitMock.mockResolvedValue([
      { user_id: 'u-2', full_name: 'Test User', role_name: 'Admin' },
    ]);
    addUnitMemberMock.mockResolvedValue(undefined);
    createUnitMock.mockResolvedValue(undefined);
    removeUnitMemberMock.mockResolvedValue(undefined);
    updateUnitMock.mockResolvedValue(undefined);
  });

  it('loads tree and enables root creation for superadmin with permission', async () => {
    const { result } = renderHook(() => useUnitHierarchyPage());

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(getUnitsTreeMock).toHaveBeenCalledTimes(1);
    expect(getRecommendedUnitsTreeMock).toHaveBeenCalledTimes(1);
    expect(result.current.tree).toEqual(treeResponse);
    expect(result.current.recommendedTree).toHaveLength(1);
    expect(result.current.canCreateRootUnit).toBe(true);
  });

  it('adds a member to the selected unit and reloads the tree', async () => {
    const { result } = renderHook(() => useUnitHierarchyPage());

    await waitFor(() => expect(result.current.tree).toHaveLength(1));

    act(() => {
      result.current.openMemberDialog(result.current.tree[0]!);
    });

    await waitFor(() => expect(getAvailableUsersForUnitMock).toHaveBeenCalledWith(1, ''));

    act(() => {
      result.current.setSelectedUserId('u-2');
    });

    await act(async () => {
      await result.current.submitMember();
    });

    expect(addUnitMemberMock).toHaveBeenCalledWith(1, 'u-2');
    expect(showSuccessToastMock).toHaveBeenCalledTimes(1);
    expect(getUnitsTreeMock).toHaveBeenCalledTimes(2);
  });
});
