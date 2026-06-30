import { useCallback, useDeferredValue, useEffect, useMemo, useState } from 'react';
import { useAuth } from '@app/providers/AuthProvider';
import { hasPermission } from '@shared/auth/permissions';
import { ROLE } from '@shared/constants/roles';
import {
  addUnitMember,
  createUnit,
  deleteUnit,
  getAvailableUsersForUnit,
  getUnassignedUsers,
  getUnitsTree,
  removeUnitMember,
  updateUnit,
  type AvailableUnitUser,
  type UnitMember,
  type UnitNode,
} from '@shared/api/units';
import { useSystemToasts } from '@shared/ui/toasts';

type UnitDialogMode = 'create-root' | 'create-child' | 'edit' | null;

type UnitDialogState = {
  mode: UnitDialogMode;
  unit: UnitNode | null;
};

type MemberDialogState = {
  unit: UnitNode | null;
  search: string;
  selectedUserId: string;
};

type MoveMemberState = {
  member: UnitMember;
  fromUnit: UnitNode;
  targetUnitId: number | null;
} | null;

type AssignMemberState = {
  user: { user_id: string; full_name: string | null };
  targetUnitId: number | null;
} | null;

type DeleteDialogState = {
  unit: UnitNode;
  previewTree: UnitNode[];
  willReassign: boolean;
} | null;

const flattenUnits = (nodes: UnitNode[]): UnitNode[] =>
  nodes.flatMap((node) => [node, ...flattenUnits(node.children)]);

const findUnitById = (nodes: UnitNode[], unitId: number): UnitNode | null => {
  for (const node of nodes) {
    if (node.unit_id === unitId) {
      return node;
    }
    const childMatch = findUnitById(node.children, unitId);
    if (childMatch) {
      return childMatch;
    }
  }
  return null;
};

const findParentUnit = (nodes: UnitNode[], unitId: number): UnitNode | null => {
  for (const node of nodes) {
    if (node.children.some((child) => child.unit_id === unitId)) {
      return node;
    }
    const nestedMatch = findParentUnit(node.children, unitId);
    if (nestedMatch) {
      return nestedMatch;
    }
  }
  return null;
};

const collectDescendantUnitIds = (unit: UnitNode): Set<number> => {
  const ids = new Set<number>();
  const visit = (node: UnitNode) => {
    ids.add(node.unit_id);
    node.children.forEach(visit);
  };
  visit(unit);
  return ids;
};

const findRootUnitForUnit = (nodes: UnitNode[], unitId: number): UnitNode | null => {
  for (const root of nodes) {
    if (findUnitById([root], unitId)) {
      return root;
    }
  }
  return null;
};

const buildUnitPathLabel = (nodes: UnitNode[], unitId: number): string => {
  const path: string[] = [];

  const visit = (list: UnitNode[], nextPath: string[]): boolean => {
    for (const unit of list) {
      const currentPath = [...nextPath, unit.name];
      if (unit.unit_id === unitId) {
        path.push(...currentPath);
        return true;
      }
      if (visit(unit.children, currentPath)) {
        return true;
      }
    }
    return false;
  };

  visit(nodes, []);
  return path.join(' / ');
};

const buildUniqueMembers = (root: UnitNode | null, includeContractors: boolean): UnitMember[] => {
  if (!root) {
    return [];
  }

  const byUserId = new Map<string, UnitMember>();
  flattenUnits([root]).forEach((unit) => {
    unit.members.forEach((member) => {
      const isContractor = member.role_id === ROLE.CONTRACTOR;
      if (includeContractors !== isContractor) {
        return;
      }
      if (!byUserId.has(member.user_id)) {
        byUserId.set(member.user_id, member);
      }
    });
  });

  return [...byUserId.values()].sort((left, right) => {
    const leftLabel = (left.full_name ?? left.user_id).toLocaleLowerCase('ru');
    const rightLabel = (right.full_name ?? right.user_id).toLocaleLowerCase('ru');
    return leftLabel.localeCompare(rightLabel, 'ru');
  });
};

const buildDeletePreviewTree = (tree: UnitNode[], unitId: number): UnitNode[] => {
  const cloneNode = (node: UnitNode): UnitNode => ({
    ...node,
    members: [...node.members],
    children: node.children.map(cloneNode),
    actions: { ...node.actions },
  });

  const clonedTree = tree.map(cloneNode);
  const unit = findUnitById(clonedTree, unitId);
  const parent = findParentUnit(clonedTree, unitId);
  if (!unit || !parent) {
    return clonedTree;
  }

  parent.members = [...parent.members, ...unit.members];
  parent.children = parent.children.flatMap((child) => (
    child.unit_id === unitId
      ? unit.children.map((grandChild) => ({ ...grandChild, id_parent: parent.unit_id }))
      : [child]
  ));

  return clonedTree;
};

const buildUnitOptions = (nodes: UnitNode[], path: string[] = []): Array<{ unitId: number; label: string }> =>
  nodes.flatMap((unit) => {
    const nextPath = [...path, unit.name];
    return [
      { unitId: unit.unit_id, label: nextPath.join(' / ') },
      ...buildUnitOptions(unit.children, nextPath),
    ];
  });

export const useUnitHierarchyPage = () => {
  const { session } = useAuth();
  const { showErrorToast, showSuccessToast } = useSystemToasts();

  const [tree, setTree] = useState<UnitNode[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDepartmentId, setSelectedDepartmentId] = useState<number | null>(null);
  const [selectedEditorUnitId, setSelectedEditorUnitId] = useState<number | null>(null);
  const [activeUnitDetailsId, setActiveUnitDetailsId] = useState<number | null>(null);
  const [unitDialogState, setUnitDialogState] = useState<UnitDialogState>({ mode: null, unit: null });
  const [isSavingUnit, setIsSavingUnit] = useState(false);
  const [memberDialogState, setMemberDialogState] = useState<MemberDialogState>({
    unit: null,
    search: '',
    selectedUserId: '',
  });
  const [availableUsers, setAvailableUsers] = useState<AvailableUnitUser[]>([]);
  const [isLoadingUsers, setIsLoadingUsers] = useState(false);
  const [isSavingMember, setIsSavingMember] = useState(false);
  const [moveMemberState, setMoveMemberState] = useState<MoveMemberState>(null);
  const [isMovingMember, setIsMovingMember] = useState(false);
  const [deleteDialogState, setDeleteDialogState] = useState<DeleteDialogState>(null);
  const [isDeletingUnit, setIsDeletingUnit] = useState(false);
  const [contractorDialogUnit, setContractorDialogUnit] = useState<UnitNode | null>(null);
  const [isSavingUnitNameId, setIsSavingUnitNameId] = useState<number | null>(null);
  const [unassignedUsers, setUnassignedUsers] = useState<AvailableUnitUser[]>([]);
  const [isLoadingUnassignedUsers, setIsLoadingUnassignedUsers] = useState(false);
  const [assignMemberState, setAssignMemberState] = useState<AssignMemberState>(null);
  const [isAssigningMember, setIsAssigningMember] = useState(false);
  const deferredMemberSearch = useDeferredValue(memberDialogState.search);

  const canCreateRootUnit = hasPermission(session, 'units.create') && session?.roleId === ROLE.SUPERADMIN;

  const departments = useMemo(
    () => tree.filter((unit) => unit.id_parent === null),
    [tree]
  );

  const selectedDepartment = useMemo(() => {
    if (departments.length === 0) {
      return null;
    }
    if (selectedDepartmentId === null) {
      return departments[0] ?? null;
    }
    return departments.find((department) => department.unit_id === selectedDepartmentId) ?? departments[0] ?? null;
  }, [departments, selectedDepartmentId]);

  const editorRootUnit = useMemo(
    () => (selectedEditorUnitId !== null ? findUnitById(tree, selectedEditorUnitId) : null),
    [selectedEditorUnitId, tree]
  );

  const activeUnitDetails = useMemo(
    () => (activeUnitDetailsId !== null ? findUnitById(tree, activeUnitDetailsId) : null),
    [activeUnitDetailsId, tree]
  );

  const departmentStaff = useMemo(
    () => buildUniqueMembers(selectedDepartment, false),
    [selectedDepartment]
  );

  const departmentContractors = useMemo(
    () => buildUniqueMembers(selectedDepartment, true),
    [selectedDepartment]
  );

  const selectedDepartmentUnitOptions = useMemo(
    () => (selectedDepartment ? buildUnitOptions([selectedDepartment]) : []),
    [selectedDepartment]
  );

  const moveMemberRootUnit = useMemo(() => {
    if (!moveMemberState) {
      return null;
    }

    return findRootUnitForUnit(tree, moveMemberState.fromUnit.unit_id);
  }, [moveMemberState, tree]);

  const moveUnitOptions = useMemo(() => {
    if (!moveMemberState || !moveMemberRootUnit) {
      return [];
    }

    return buildUnitOptions([moveMemberRootUnit])
      .filter((option) => option.unitId !== moveMemberState.fromUnit.unit_id)
      .map((option) => ({
        unitId: option.unitId,
        label: option.label,
      }));
  }, [moveMemberRootUnit, moveMemberState]);

  const assignUnitOptions = useMemo(() => buildUnitOptions(tree), [tree]);

  const activeUnitParent = useMemo(
    () => (activeUnitDetails ? findParentUnit(tree, activeUnitDetails.unit_id) : null),
    [activeUnitDetails, tree]
  );

  const activeUnitPathLabel = useMemo(
    () => (activeUnitDetails ? buildUnitPathLabel(tree, activeUnitDetails.unit_id) : ''),
    [activeUnitDetails, tree]
  );

  const editableParentOptions = useMemo(() => {
    if (unitDialogState.mode !== 'edit' || !unitDialogState.unit || !selectedDepartment) {
      return [];
    }

    const blockedIds = collectDescendantUnitIds(unitDialogState.unit);
    return buildUnitOptions([selectedDepartment]).filter((option) => !blockedIds.has(option.unitId));
  }, [selectedDepartment, unitDialogState]);

  const loadUnassignedUsers = useCallback(async () => {
    setIsLoadingUnassignedUsers(true);
    try {
      const items = await getUnassignedUsers();
      setUnassignedUsers(items);
    } catch {
      setUnassignedUsers([]);
    } finally {
      setIsLoadingUnassignedUsers(false);
    }
  }, []);

  const loadTree = useCallback(async (preserveSelection = true) => {
    setIsLoading(true);
    setError(null);
    void loadUnassignedUsers();
    try {
      const nextTree = await getUnitsTree();
      setTree(nextTree);

      const nextDepartments = nextTree.filter((unit) => unit.id_parent === null);
      if (nextDepartments.length === 0) {
        setSelectedDepartmentId(null);
        setSelectedEditorUnitId(null);
        setActiveUnitDetailsId(null);
        return;
      }

      if (!preserveSelection || selectedDepartmentId === null || !findUnitById(nextDepartments, selectedDepartmentId)) {
        setSelectedDepartmentId(nextDepartments[0]!.unit_id);
      }

      if (selectedEditorUnitId !== null && !findUnitById(nextTree, selectedEditorUnitId)) {
        setSelectedEditorUnitId(null);
      }

      if (activeUnitDetailsId !== null && !findUnitById(nextTree, activeUnitDetailsId)) {
        setActiveUnitDetailsId(null);
      }
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Не удалось загрузить иерархию подразделений');
    } finally {
      setIsLoading(false);
    }
  }, [activeUnitDetailsId, loadUnassignedUsers, selectedDepartmentId, selectedEditorUnitId]);

  useEffect(() => {
    void loadTree(false);
  }, [loadTree]);

  useEffect(() => {
    if (!memberDialogState.unit) {
      return;
    }

    let cancelled = false;
    const loadUsers = async () => {
      setIsLoadingUsers(true);
      try {
        const items = await getAvailableUsersForUnit(memberDialogState.unit!.unit_id, deferredMemberSearch);
        if (!cancelled) {
          setAvailableUsers(items);
        }
      } catch (loadError) {
        if (!cancelled) {
          setAvailableUsers([]);
          showErrorToast(loadError instanceof Error ? loadError.message : 'Не удалось загрузить сотрудников');
        }
      } finally {
        if (!cancelled) {
          setIsLoadingUsers(false);
        }
      }
    };

    void loadUsers();
    return () => {
      cancelled = true;
    };
  }, [deferredMemberSearch, memberDialogState.unit, showErrorToast]);

  const openCreateRootDialog = () => setUnitDialogState({ mode: 'create-root', unit: null });
  const openCreateChildDialog = (unit: UnitNode) => setUnitDialogState({ mode: 'create-child', unit });
  const openEditUnitDialog = (unit: UnitNode) => setUnitDialogState({ mode: 'edit', unit });
  const closeUnitDialog = () => setUnitDialogState({ mode: null, unit: null });

  const submitUnit = async (payload: { name: string; parentUnitId?: number | null }) => {
    const normalizedName = payload.name.trim();
    if (!normalizedName) {
      showErrorToast('Название подразделения обязательно');
      return;
    }

    setIsSavingUnit(true);
    try {
      if (unitDialogState.mode === 'edit' && unitDialogState.unit) {
        await updateUnit(unitDialogState.unit.unit_id, {
          name: normalizedName,
          id_parent: payload.parentUnitId ?? unitDialogState.unit.id_parent ?? undefined,
        });
        showSuccessToast('Подразделение обновлено');
      } else {
        const createdUnit = await createUnit({
          name: normalizedName,
          id_parent: unitDialogState.mode === 'create-child' && unitDialogState.unit
            ? unitDialogState.unit.unit_id
            : undefined,
        });
        if (createdUnit.id_parent === selectedDepartment?.unit_id) {
          setSelectedEditorUnitId(createdUnit.unit_id);
        }
        showSuccessToast(unitDialogState.mode === 'create-root' ? 'Подразделение создано' : 'Лист создан');
      }

      closeUnitDialog();
      await loadTree();
    } catch (submitError) {
      showErrorToast(submitError instanceof Error ? submitError.message : 'Не удалось сохранить подразделение');
    } finally {
      setIsSavingUnit(false);
    }
  };

  const openMemberDialog = (unit: UnitNode) => {
    setMemberDialogState({ unit, search: '', selectedUserId: '' });
    setAvailableUsers([]);
  };

  const closeMemberDialog = () => {
    setMemberDialogState({ unit: null, search: '', selectedUserId: '' });
    setAvailableUsers([]);
  };

  const submitMember = async () => {
    if (!memberDialogState.unit || !memberDialogState.selectedUserId) {
      showErrorToast('Выберите сотрудника');
      return;
    }

    setIsSavingMember(true);
    try {
      await addUnitMember(memberDialogState.unit.unit_id, memberDialogState.selectedUserId);
      showSuccessToast('Сотрудник добавлен в подразделение');
      closeMemberDialog();
      await loadTree();
    } catch (submitError) {
      showErrorToast(submitError instanceof Error ? submitError.message : 'Не удалось добавить сотрудника');
    } finally {
      setIsSavingMember(false);
    }
  };

  const removeMemberFromUnit = async (unit: UnitNode, member: UnitMember) => {
    try {
      await removeUnitMember(unit.unit_id, member.user_id);
      showSuccessToast('Сотрудник откреплен от подразделения');
      if (moveMemberState?.member.user_id === member.user_id && moveMemberState.fromUnit.unit_id === unit.unit_id) {
        setMoveMemberState(null);
      }
      await loadTree();
    } catch (removeError) {
      showErrorToast(removeError instanceof Error ? removeError.message : 'Не удалось открепить сотрудника');
    }
  };

  const openContractorDialog = (unit: UnitNode) => {
    setContractorDialogUnit(unit);
  };

  const closeContractorDialog = () => {
    setContractorDialogUnit(null);
  };

  const removeContractorFromUnit = async (unit: UnitNode, member: UnitMember) => {
    try {
      await removeUnitMember(unit.unit_id, member.user_id);
      showSuccessToast('Контрагент откреплен от подразделения');
      await loadTree();
    } catch (removeError) {
      showErrorToast(removeError instanceof Error ? removeError.message : 'Не удалось открепить контрагента');
    }
  };

  const openMoveMemberDialog = (unit: UnitNode, member: UnitMember) => {
    setMoveMemberState({ member, fromUnit: unit, targetUnitId: null });
  };

  const closeMoveMemberDialog = () => setMoveMemberState(null);

  const submitMoveMember = async () => {
    if (!moveMemberState || moveMemberState.targetUnitId === null) {
      showErrorToast('Выберите целевое подразделение');
      return;
    }

    setIsMovingMember(true);
    try {
      await addUnitMember(moveMemberState.targetUnitId, moveMemberState.member.user_id);
      await removeUnitMember(moveMemberState.fromUnit.unit_id, moveMemberState.member.user_id);
      showSuccessToast('Сотрудник перенесен в другое подразделение');
      closeMoveMemberDialog();
      await loadTree();
    } catch (moveError) {
      showErrorToast(moveError instanceof Error ? moveError.message : 'Не удалось перенести сотрудника');
    } finally {
      setIsMovingMember(false);
    }
  };

  const openAssignMemberDialog = (user: { user_id: string; full_name: string | null }) => {
    setAssignMemberState({ user, targetUnitId: null });
  };

  const closeAssignMemberDialog = () => setAssignMemberState(null);

  const submitAssignMember = async () => {
    if (!assignMemberState || assignMemberState.targetUnitId === null) {
      showErrorToast('Выберите подразделение');
      return;
    }

    setIsAssigningMember(true);
    try {
      await addUnitMember(assignMemberState.targetUnitId, assignMemberState.user.user_id);
      showSuccessToast('Сотрудник определён в подразделение');
      closeAssignMemberDialog();
      await loadTree();
    } catch (submitError) {
      showErrorToast(submitError instanceof Error ? submitError.message : 'Не удалось определить сотрудника');
    } finally {
      setIsAssigningMember(false);
    }
  };

  const submitUnitName = async (unit: UnitNode, nextName: string) => {
    const normalizedName = nextName.trim();
    if (!normalizedName) {
      showErrorToast('Название подразделения обязательно');
      return;
    }

    if (normalizedName === unit.name) {
      return;
    }

    setIsSavingUnitNameId(unit.unit_id);
    try {
      await updateUnit(unit.unit_id, {
        name: normalizedName,
        id_parent: unit.id_parent ?? undefined,
      });
      showSuccessToast('Подразделение обновлено');
      await loadTree();
    } catch (submitError) {
      showErrorToast(submitError instanceof Error ? submitError.message : 'Не удалось сохранить подразделение');
    } finally {
      setIsSavingUnitNameId(null);
    }
  };

  const openDeleteDialog = (unit: UnitNode) => {
    const previewTree = buildDeletePreviewTree(tree, unit.unit_id);
    setDeleteDialogState({
      unit,
      previewTree,
      willReassign: unit.id_parent !== null && (unit.members.length > 0 || unit.children.length > 0),
    });
  };

  const closeDeleteDialog = () => setDeleteDialogState(null);

  const confirmDeleteUnit = async () => {
    if (!deleteDialogState) {
      return;
    }

    setIsDeletingUnit(true);
    try {
      await deleteUnit(deleteDialogState.unit.unit_id, deleteDialogState.willReassign);
      showSuccessToast('Подразделение удалено');
      if (selectedEditorUnitId === deleteDialogState.unit.unit_id) {
        setSelectedEditorUnitId(null);
      }
      if (activeUnitDetailsId === deleteDialogState.unit.unit_id) {
        setActiveUnitDetailsId(null);
      }
      closeDeleteDialog();
      await loadTree();
    } catch (deleteError) {
      showErrorToast(deleteError instanceof Error ? deleteError.message : 'Не удалось удалить подразделение');
    } finally {
      setIsDeletingUnit(false);
    }
  };

  return {
    tree,
    departments,
    isLoading,
    error,
    selectedDepartment,
    selectedDepartmentId,
    setSelectedDepartmentId,
    selectedEditorUnitId,
    setSelectedEditorUnitId,
    editorRootUnit,
    departmentStaff,
    departmentContractors,
    selectedDepartmentUnitOptions,
    canCreateRootUnit,
    activeUnitDetails,
    activeUnitParent,
    activeUnitPathLabel,
    setActiveUnitDetailsId,
    unitDialogState,
    isSavingUnit,
    editableParentOptions,
    openCreateRootDialog,
    openCreateChildDialog,
    openEditUnitDialog,
    closeUnitDialog,
    submitUnit,
    memberDialogState,
    setMemberDialogState,
    availableUsers,
    isLoadingUsers,
    isSavingMember,
    openMemberDialog,
    closeMemberDialog,
    submitMember,
    removeMemberFromUnit,
    contractorDialogUnit,
    openContractorDialog,
    closeContractorDialog,
    removeContractorFromUnit,
    moveMemberState,
    moveUnitOptions,
    setMoveMemberState,
    isMovingMember,
    openMoveMemberDialog,
    closeMoveMemberDialog,
    submitMoveMember,
    isSavingUnitNameId,
    submitUnitName,
    deleteDialogState,
    isDeletingUnit,
    openDeleteDialog,
    closeDeleteDialog,
    confirmDeleteUnit,
    loadTree,
    unassignedUsers,
    isLoadingUnassignedUsers,
    assignMemberState,
    setAssignMemberState,
    isAssigningMember,
    assignUnitOptions,
    openAssignMemberDialog,
    closeAssignMemberDialog,
    submitAssignMember,
    findRootUnitForUnit: (unitId: number) => findRootUnitForUnit(tree, unitId),
  };
};
