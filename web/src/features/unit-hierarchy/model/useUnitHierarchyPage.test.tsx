import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ROLE } from '@shared/constants/roles';
import type { UnitNode } from '@shared/api/units';
import { useUnitHierarchyPage } from './useUnitHierarchyPage';

const useAuthMock = vi.fn();
const getUnitsTreeMock = vi.fn();
const getAvailableUsersForUnitMock = vi.fn();
const getUnassignedUsersMock = vi.fn();
const addUnitMemberMock = vi.fn();
const createUnitMock = vi.fn();
const deleteUnitMock = vi.fn();
const removeUnitMemberMock = vi.fn();
const updateUnitMock = vi.fn();
const showErrorToastMock = vi.fn();
const showSuccessToastMock = vi.fn();

vi.mock('@app/providers/AuthProvider', () => ({
  useAuth: () => useAuthMock(),
}));

vi.mock('@shared/api/units', () => ({
  getUnitsTree: (...args: unknown[]) => getUnitsTreeMock(...args),
  getAvailableUsersForUnit: (...args: unknown[]) => getAvailableUsersForUnitMock(...args),
  getUnassignedUsers: (...args: unknown[]) => getUnassignedUsersMock(...args),
  addUnitMember: (...args: unknown[]) => addUnitMemberMock(...args),
  createUnit: (...args: unknown[]) => createUnitMock(...args),
  deleteUnit: (...args: unknown[]) => deleteUnitMock(...args),
  removeUnitMember: (...args: unknown[]) => removeUnitMemberMock(...args),
  updateUnit: (...args: unknown[]) => updateUnitMock(...args),
}));

vi.mock('@shared/ui/toasts', () => ({
  useSystemToasts: () => ({
    showErrorToast: showErrorToastMock,
    showSuccessToast: showSuccessToastMock,
  }),
}));

const treeResponse: UnitNode[] = [
  {
    unit_id: 1,
    name: 'Финансы',
    id_parent: null,
    is_active: true,
    members: [],
    children: [
      {
        unit_id: 2,
        name: 'Проект А',
        id_parent: 1,
        is_active: true,
        members: [
          {
            user_id: 'econ-1',
            id_parent_user: null,
            full_name: 'Экономист 1',
            role_id: ROLE.ECONOMIST,
            role_name: 'Экономист',
            status: 'active',
          },
        ],
        children: [],
        actions: {
          canCreateChild: true,
          canUpdate: true,
          canDelete: true,
          canManageMembers: true,
        },
      },
    ],
    actions: {
      canCreateChild: true,
      canUpdate: true,
      canDelete: false,
      canManageMembers: true,
    },
  },
];

const multiDepartmentTreeResponse = [
  {
    unit_id: 1,
    name: 'Финансы',
    id_parent: null,
    is_active: true,
    members: [],
    children: [
      {
        unit_id: 2,
        name: 'Проект А',
        id_parent: 1,
        is_active: true,
        members: [],
        children: [],
        actions: {
          canCreateChild: true,
          canUpdate: true,
          canDelete: true,
          canManageMembers: true,
        },
      },
    ],
    actions: {
      canCreateChild: true,
      canUpdate: true,
      canDelete: false,
      canManageMembers: true,
    },
  },
  {
    unit_id: 10,
    name: 'АО',
    id_parent: null,
    is_active: true,
    members: [],
    children: [
      {
        unit_id: 11,
        name: 'Модуль 2',
        id_parent: 10,
        is_active: true,
        members: [
          {
            user_id: 'econ-9',
            full_name: 'Иванова Ольга Игоревна',
            role_id: ROLE.ECONOMIST,
            role_name: 'Экономист',
            status: 'active',
          },
        ],
        children: [],
        actions: {
          canCreateChild: true,
          canUpdate: true,
          canDelete: true,
          canManageMembers: true,
        },
      },
      {
        unit_id: 12,
        name: 'Модуль 2.1',
        id_parent: 10,
        is_active: true,
        members: [],
        children: [
          {
            unit_id: 13,
            name: 'Модуль 2.1.1',
            id_parent: 12,
            is_active: true,
            members: [],
            children: [],
            actions: {
              canCreateChild: true,
              canUpdate: true,
              canDelete: true,
              canManageMembers: true,
            },
          },
        ],
        actions: {
          canCreateChild: true,
          canUpdate: true,
          canDelete: true,
          canManageMembers: true,
        },
      },
    ],
    actions: {
      canCreateChild: true,
      canUpdate: true,
      canDelete: false,
      canManageMembers: true,
    },
  },
];

describe('useUnitHierarchyPage', () => {
  beforeEach(() => {
    useAuthMock.mockReset();
    getUnitsTreeMock.mockReset();
    getAvailableUsersForUnitMock.mockReset();
    getUnassignedUsersMock.mockReset();
    getUnassignedUsersMock.mockResolvedValue([]);
    addUnitMemberMock.mockReset();
    createUnitMock.mockReset();
    deleteUnitMock.mockReset();
    removeUnitMemberMock.mockReset();
    updateUnitMock.mockReset();
    showErrorToastMock.mockReset();
    showSuccessToastMock.mockReset();

    useAuthMock.mockReturnValue({
      session: {
        roleId: ROLE.SUPERADMIN,
        permissions: ['units.read', 'units.create', 'units.update', 'units.members.manage'],
      },
    });
    getUnitsTreeMock.mockResolvedValue(treeResponse);
    getAvailableUsersForUnitMock.mockResolvedValue([
      {
        user_id: 'econ-2',
        full_name: 'Экономист 2',
        role_id: ROLE.ECONOMIST,
        role_name: 'Экономист',
        status: 'active',
      },
    ]);
    createUnitMock.mockResolvedValue({
      unit_id: 3,
      name: 'Проект Б',
      id_parent: 1,
      is_active: true,
      members: [],
      children: [],
      actions: {
        canCreateChild: true,
        canUpdate: true,
        canDelete: true,
        canManageMembers: true,
      },
    });
    addUnitMemberMock.mockResolvedValue(undefined);
    removeUnitMemberMock.mockResolvedValue(undefined);
    updateUnitMock.mockResolvedValue(undefined);
    deleteUnitMock.mockResolvedValue(undefined);
  });

  it('loads departments and exposes selected department context', async () => {
    const { result } = renderHook(() => useUnitHierarchyPage());

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(getUnitsTreeMock).toHaveBeenCalledTimes(1);
    expect(result.current.departments).toHaveLength(1);
    expect(result.current.selectedDepartment?.name).toBe('Финансы');
    expect(result.current.departmentStaff).toHaveLength(1);
    expect(result.current.canCreateRootUnit).toBe(true);
  });

  it.each([
    { editorUnitId: null, parentUnitId: 1 },
    { editorUnitId: 1, parentUnitId: 1 },
    { editorUnitId: 2, parentUnitId: 2 },
  ])('creates a child of $parentUnitId without changing the current chart ($editorUnitId)', async ({ editorUnitId, parentUnitId }) => {
    const { result } = renderHook(() => useUnitHierarchyPage());

    await waitFor(() => expect(result.current.selectedDepartment?.unit_id).toBe(1));

    const parent = parentUnitId === 1 ? treeResponse[0]! : treeResponse[0]!.children[0]!;
    const child = { ...parent, unit_id: 3, name: 'Проект Б', id_parent: parentUnitId, members: [], children: [] };
    const refreshedTree = structuredClone(treeResponse);
    const refreshedParent = parentUnitId === 1 ? refreshedTree[0]! : refreshedTree[0]!.children[0]!;
    refreshedParent.children.push(child);
    createUnitMock.mockResolvedValue(child);
    let resolveRefresh!: (tree: typeof treeResponse) => void;
    getUnitsTreeMock.mockImplementationOnce(() => new Promise<typeof treeResponse>((resolve) => {
      resolveRefresh = resolve;
    }));

    act(() => {
      result.current.setSelectedEditorUnitId(editorUnitId);
      result.current.setActiveUnitDetailsId(parentUnitId);
      result.current.openCreateChildDialog(parent);
    });

    let submission!: Promise<void>;
    act(() => {
      submission = result.current.submitUnit({ name: 'Проект Б' });
    });
    await waitFor(() => expect(getUnitsTreeMock).toHaveBeenCalledTimes(2));

    // A pending refresh must not unmount the chart or navigate to the new child.
    expect(result.current.isLoading).toBe(false);
    expect(result.current.selectedEditorUnitId).toBe(editorUnitId);
    expect(result.current.activeUnitDetails?.unit_id).toBe(parentUnitId);

    await act(async () => {
      resolveRefresh(refreshedTree);
      await submission;
    });

    expect(createUnitMock).toHaveBeenCalledWith({ name: 'Проект Б', id_parent: parentUnitId });
    expect(showSuccessToastMock).toHaveBeenCalledWith('Объединение создано');
    expect(result.current.selectedEditorUnitId).toBe(editorUnitId);
    expect(result.current.selectedDepartmentId).toBe(1);
    expect(result.current.activeUnitDetails?.children).toContainEqual(child);
    expect(result.current.unitDialogState.mode).toBeNull();
  });

  it('adds a member into the active unit', async () => {
    const { result } = renderHook(() => useUnitHierarchyPage());

    await waitFor(() => expect(result.current.selectedDepartment?.unit_id).toBe(1));

    act(() => {
      result.current.openMemberDialog(result.current.selectedDepartment!.children[0]!);
    });

    await waitFor(() => expect(getAvailableUsersForUnitMock).toHaveBeenCalledWith(2, ''));

    act(() => {
      result.current.setMemberDialogState((current) => ({ ...current, selectedUserId: 'econ-2' }));
    });

    await act(async () => {
      await result.current.submitMember();
    });

    expect(addUnitMemberMock).toHaveBeenCalledWith(2, 'econ-2');
    expect(showSuccessToastMock).toHaveBeenCalledWith('Сотрудник добавлен в объединение');
  });

  it('opens delete dialog with reassignment preview for non-empty unit', async () => {
    const { result } = renderHook(() => useUnitHierarchyPage());

    await waitFor(() => expect(result.current.selectedDepartment?.unit_id).toBe(1));

    act(() => {
      result.current.openDeleteDialog(result.current.selectedDepartment!.children[0]!);
    });

    expect(result.current.deleteDialogState?.willReassign).toBe(true);

    await act(async () => {
      await result.current.confirmDeleteUnit();
    });

    expect(deleteUnitMock).toHaveBeenCalledWith(2, true);
    expect(showSuccessToastMock).toHaveBeenCalledWith('Объединение удалено');
  });
  it('builds move targets from all manageable units except the source unit', async () => {
    getUnitsTreeMock.mockResolvedValue(multiDepartmentTreeResponse);

    const { result } = renderHook(() => useUnitHierarchyPage());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.selectedDepartment?.name).toBe('Финансы');
    expect(result.current.departments).toHaveLength(2);

    const module2 = result.current.departments[1]!.children[0]!;
    const member = module2.members[0]!;

    act(() => {
      result.current.openMoveMemberDialog(module2, member);
    });

    expect(result.current.moveUnitOptions).toEqual([
      { unitId: 1, label: 'Финансы' },
      { unitId: 2, label: 'Финансы / Проект А' },
      { unitId: 10, label: 'АО' },
      { unitId: 12, label: 'АО / Модуль 2.1' },
      { unitId: 13, label: 'АО / Модуль 2.1 / Модуль 2.1.1' },
    ]);
  });
});
