import { useCallback, useDeferredValue, useEffect, useMemo, useState } from 'react';
import { useAuth } from '@app/providers/AuthProvider';
import { hasPermission } from '@shared/auth/permissions';
import { ROLE } from '@shared/constants/roles';
import {
  addUnitMember,
  createUnit,
  getAvailableUsersForUnit,
  getRecommendedUnitsTree,
  getUnitsTree,
  removeUnitMember,
  updateUnit,
  type AvailableUnitUser,
  type RecommendedHierarchyNode,
  type UnitMember,
  type UnitNode,
} from '@shared/api/units';
import { useSystemToasts } from '@shared/ui/toasts';

type UnitDialogMode = 'create-root' | 'create-child' | 'rename' | null;

type UnitOption = {
  label: string;
  unitId: number;
};

type AssignedUnitInfo = UnitOption & {
  depth: number;
  unitName: string;
};

type RecommendedAssignmentCandidate = {
  full_name: string | null;
  parentDisplayName: string | null;
  role_id: number;
  role_name: string;
  status: string;
  user_id: string;
};

const flattenUnitIds = (nodes: UnitNode[]): number[] =>
  nodes.flatMap((node) => [node.unit_id, ...flattenUnitIds(node.children)]);

const flattenUnitMembers = (nodes: UnitNode[]): UnitMember[] =>
  nodes.flatMap((node) => [...node.members, ...flattenUnitMembers(node.children)]);

const buildUnitOptions = (nodes: UnitNode[], path: string[] = []): UnitOption[] =>
  nodes.flatMap((node) => {
    const nextPath = [...path, node.name];
    return [
      {
        unitId: node.unit_id,
        label: nextPath.join(' / '),
      },
      ...buildUnitOptions(node.children, nextPath),
    ];
  });

const buildMemberUnitMap = (
  nodes: UnitNode[],
  path: string[] = [],
  depth = 0,
  accumulator: Record<string, AssignedUnitInfo[]> = {}
): Record<string, AssignedUnitInfo[]> => {
  nodes.forEach((node) => {
    const nextPath = [...path, node.name];
    const currentUnit: AssignedUnitInfo = {
      unitId: node.unit_id,
      label: nextPath.join(' / '),
      unitName: node.name,
      depth,
    };

    node.members.forEach((member) => {
      const currentAssignments = accumulator[member.user_id] ?? [];
      accumulator[member.user_id] = [...currentAssignments, currentUnit];
    });

    buildMemberUnitMap(node.children, nextPath, depth + 1, accumulator);
  });

  Object.keys(accumulator).forEach((userId) => {
    accumulator[userId] = accumulator[userId]!
      .slice()
      .sort((left, right) => left.depth - right.depth || left.unitName.localeCompare(right.unitName, 'ru'));
  });

  return accumulator;
};

const isRecommendedPlaceholder = (node: RecommendedHierarchyNode) => {
  const normalizedName = (node.full_name ?? '').trim().toLowerCase();
  return normalizedName.includes('вакан') || normalizedName.includes('не указано');
};

const collectRecommendedAssignmentCandidates = (
  nodes: RecommendedHierarchyNode[],
  assignedUserIds: Set<string>,
  parentDisplayName: string | null = null
): RecommendedAssignmentCandidate[] =>
  nodes.flatMap((node) => {
    const nextParentDisplayName = node.full_name?.trim() || node.user_id;
    const ownCandidate = !assignedUserIds.has(node.user_id) && !isRecommendedPlaceholder(node)
      ? [{
        user_id: node.user_id,
        full_name: node.full_name,
        role_id: node.role_id,
        role_name: node.role_name,
        status: node.status,
        parentDisplayName,
      }]
      : [];

    return [
      ...ownCandidate,
      ...collectRecommendedAssignmentCandidates(node.children, assignedUserIds, nextParentDisplayName),
    ];
  });

export const useUnitHierarchyPage = () => {
  const { session } = useAuth();
  const { showErrorToast, showSuccessToast } = useSystemToasts();
  const [tree, setTree] = useState<UnitNode[]>([]);
  const [recommendedTree, setRecommendedTree] = useState<RecommendedHierarchyNode[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [recommendedError, setRecommendedError] = useState<string | null>(null);
  const [unitDialogMode, setUnitDialogMode] = useState<UnitDialogMode>(null);
  const [activeUnit, setActiveUnit] = useState<UnitNode | null>(null);
  const [unitName, setUnitName] = useState('');
  const [isSavingUnit, setIsSavingUnit] = useState(false);
  const [isMemberDialogOpen, setIsMemberDialogOpen] = useState(false);
  const [memberSearch, setMemberSearch] = useState('');
  const deferredMemberSearch = useDeferredValue(memberSearch);
  const [availableUsers, setAvailableUsers] = useState<AvailableUnitUser[]>([]);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [createAssigneeSearch, setCreateAssigneeSearch] = useState('');
  const deferredCreateAssigneeSearch = useDeferredValue(createAssigneeSearch);
  const [createAvailableUsers, setCreateAvailableUsers] = useState<AvailableUnitUser[]>([]);
  const [selectedCreateUserId, setSelectedCreateUserId] = useState('');
  const [isLoadingUsers, setIsLoadingUsers] = useState(false);
  const [isLoadingCreateUsers, setIsLoadingCreateUsers] = useState(false);
  const [isSavingMember, setIsSavingMember] = useState(false);
  const [isAssigningRecommendedUserId, setIsAssigningRecommendedUserId] = useState<string | null>(null);
  const [isDetachingRecommendedAssignmentKey, setIsDetachingRecommendedAssignmentKey] = useState<string | null>(null);

  const canCreateRootUnit = hasPermission(session, 'units.create') && session?.roleId === ROLE.SUPERADMIN;
  const visibleUnitIds = useMemo(() => new Set(flattenUnitIds(tree)), [tree]);
  const unitOptions = useMemo(() => buildUnitOptions(tree), [tree]);
  const memberUnitByUserId = useMemo(() => buildMemberUnitMap(tree), [tree]);
  const assignedUserIds = useMemo(
    () => new Set(flattenUnitMembers(tree).map((member) => member.user_id)),
    [tree]
  );
  const unassignedRecommendedMembers = useMemo(
    () => collectRecommendedAssignmentCandidates(recommendedTree, assignedUserIds),
    [assignedUserIds, recommendedTree]
  );
  const isCreateDialogOpen = unitDialogMode === 'create-root' || unitDialogMode === 'create-child';

  const loadTree = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      setTree(await getUnitsTree());
    } catch (loadError) {
      const message = loadError instanceof Error ? loadError.message : 'Не удалось загрузить иерархию';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadTree();
  }, [loadTree]);

  const loadRecommendedTree = useCallback(async () => {
    setRecommendedError(null);
    try {
      setRecommendedTree(await getRecommendedUnitsTree());
    } catch (loadError) {
      const message = loadError instanceof Error ? loadError.message : 'Не удалось загрузить рекомендуемую структуру';
      setRecommendedError(message);
      setRecommendedTree([]);
    }
  }, []);

  useEffect(() => {
    void loadRecommendedTree();
  }, [loadRecommendedTree]);

  const loadAvailableUsers = useCallback(async (unitId: number, searchValue?: string) => {
    setIsLoadingUsers(true);
    try {
      setAvailableUsers(await getAvailableUsersForUnit(unitId, searchValue));
    } catch (loadError) {
      const message = loadError instanceof Error ? loadError.message : 'Не удалось загрузить доступных участников';
      showErrorToast(message);
      setAvailableUsers([]);
    } finally {
      setIsLoadingUsers(false);
    }
  }, [showErrorToast]);

  const loadCreateAvailableUsers = useCallback(async (searchValue?: string) => {
    setIsLoadingCreateUsers(true);
    try {
      setCreateAvailableUsers(await getAvailableUsersForUnit(undefined, searchValue));
    } catch (loadError) {
      const message = loadError instanceof Error ? loadError.message : 'РќРµ СѓРґР°Р»РѕСЃСЊ Р·Р°РіСЂСѓР·РёС‚СЊ СЃРїРёСЃРѕРє СЃРѕС‚СЂСѓРґРЅРёРєРѕРІ';
      showErrorToast(message);
      setCreateAvailableUsers([]);
    } finally {
      setIsLoadingCreateUsers(false);
    }
  }, [showErrorToast]);

  useEffect(() => {
    if (!isMemberDialogOpen || !activeUnit) {
      return;
    }
    void loadAvailableUsers(activeUnit.unit_id, deferredMemberSearch);
  }, [activeUnit, deferredMemberSearch, isMemberDialogOpen, loadAvailableUsers]);

  useEffect(() => {
    if (!isCreateDialogOpen) {
      return;
    }
    void loadCreateAvailableUsers(deferredCreateAssigneeSearch);
  }, [deferredCreateAssigneeSearch, isCreateDialogOpen, loadCreateAvailableUsers]);

  const resetCreateDialogState = useCallback(() => {
    setUnitName('');
    setCreateAssigneeSearch('');
    setCreateAvailableUsers([]);
    setSelectedCreateUserId('');
  }, []);

  const closeUnitDialog = useCallback(() => {
    setUnitDialogMode(null);
    setActiveUnit(null);
    resetCreateDialogState();
  }, [resetCreateDialogState]);

  const openCreateRootDialog = useCallback((initialUserId?: string) => {
    setUnitDialogMode('create-root');
    setActiveUnit(null);
    resetCreateDialogState();
    setSelectedCreateUserId(initialUserId ?? '');
  }, [resetCreateDialogState]);

  const openCreateChildDialog = useCallback((unit: UnitNode, initialUserId?: string) => {
    setUnitDialogMode('create-child');
    setActiveUnit(unit);
    resetCreateDialogState();
    setSelectedCreateUserId(initialUserId ?? '');
  }, [resetCreateDialogState]);

  const openRenameDialog = useCallback((unit: UnitNode) => {
    setUnitDialogMode('rename');
    setActiveUnit(unit);
    resetCreateDialogState();
    setUnitName(unit.name);
  }, [resetCreateDialogState]);

  const submitUnit = useCallback(async () => {
    const normalizedName = unitName.trim();
    if (!normalizedName) {
      showErrorToast('Название обязательно');
      return;
    }

    setIsSavingUnit(true);
    try {
      if (unitDialogMode === 'rename' && activeUnit) {
        await updateUnit(activeUnit.unit_id, { name: normalizedName });
        showSuccessToast('Название узла обновлено');
      } else {
        const createdUnit = await createUnit({
          name: normalizedName,
          id_parent: unitDialogMode === 'create-child' && activeUnit ? activeUnit.unit_id : undefined,
        });
        if (selectedCreateUserId) {
          try {
            await addUnitMember(createdUnit.unit_id, selectedCreateUserId);
            showSuccessToast('Узел создан, сотрудник добавлен');
          } catch (assignError) {
            showSuccessToast('Узел создан');
            showErrorToast(
              assignError instanceof Error
                ? `Узел создан, но сотрудника не удалось добавить: ${assignError.message}`
                : 'Узел создан, но сотрудника не удалось добавить'
            );
            closeUnitDialog();
            await loadTree();
            return;
          }
        } else {
          showSuccessToast('Узел создан');
        }
      }
      closeUnitDialog();
      await loadTree();
    } catch (submitError) {
      showErrorToast(submitError instanceof Error ? submitError.message : 'Не удалось сохранить узел');
    } finally {
      setIsSavingUnit(false);
    }
  }, [
    activeUnit,
    closeUnitDialog,
    loadTree,
    selectedCreateUserId,
    showErrorToast,
    showSuccessToast,
    unitDialogMode,
    unitName,
  ]);

  const deactivateUnit = useCallback(async (unit: UnitNode) => {
    if (!window.confirm(`Деактивировать узел «${unit.name}»?`)) {
      return;
    }

    try {
      await updateUnit(unit.unit_id, { is_active: false });
      showSuccessToast('Узел деактивирован');
      await loadTree();
    } catch (deactivateError) {
      showErrorToast(deactivateError instanceof Error ? deactivateError.message : 'Не удалось деактивировать узел');
    }
  }, [loadTree, showErrorToast, showSuccessToast]);

  const openMemberDialog = useCallback((unit: UnitNode) => {
    setActiveUnit(unit);
    setMemberSearch('');
    setSelectedUserId('');
    setAvailableUsers([]);
    setIsMemberDialogOpen(true);
  }, []);

  const closeMemberDialog = useCallback(() => {
    setIsMemberDialogOpen(false);
    setSelectedUserId('');
    setMemberSearch('');
    setAvailableUsers([]);
  }, []);

  const submitMember = useCallback(async () => {
    if (!activeUnit || !selectedUserId) {
      showErrorToast('Выберите участника');
      return;
    }

    setIsSavingMember(true);
    try {
      await addUnitMember(activeUnit.unit_id, selectedUserId);
      showSuccessToast('Участник добавлен');
      closeMemberDialog();
      await loadTree();
    } catch (submitError) {
      showErrorToast(submitError instanceof Error ? submitError.message : 'Не удалось добавить участника');
    } finally {
      setIsSavingMember(false);
    }
  }, [activeUnit, closeMemberDialog, loadTree, selectedUserId, showErrorToast, showSuccessToast]);

  const deleteMember = useCallback(async (unit: UnitNode, member: UnitMember) => {
    if (!window.confirm(`Удалить участника «${member.full_name ?? member.user_id}» из узла «${unit.name}»?`)) {
      return;
    }

    try {
      await removeUnitMember(unit.unit_id, member.user_id);
      showSuccessToast('Участник удален из узла');
      await loadTree();
    } catch (deleteError) {
      showErrorToast(deleteError instanceof Error ? deleteError.message : 'Не удалось удалить участника');
    }
  }, [loadTree, showErrorToast, showSuccessToast]);

  const assignRecommendedMemberToUnit = useCallback(async (userId: string, unitId: number) => {
    setIsAssigningRecommendedUserId(userId);
    try {
      await addUnitMember(unitId, userId);
      showSuccessToast('Участник закреплен за выбранным узлом');
      await loadTree();
    } catch (assignError) {
      showErrorToast(assignError instanceof Error ? assignError.message : 'Не удалось закрепить участника за узлом');
    } finally {
      setIsAssigningRecommendedUserId(null);
    }
  }, [loadTree, showErrorToast, showSuccessToast]);

  const detachRecommendedMemberFromUnit = useCallback(async (userId: string, unitId: number) => {
    const assignmentKey = `${userId}:${unitId}`;
    setIsDetachingRecommendedAssignmentKey(assignmentKey);
    try {
      await removeUnitMember(unitId, userId);
      showSuccessToast('Привязка сотрудника удалена');
      await loadTree();
    } catch (detachError) {
      showErrorToast(detachError instanceof Error ? detachError.message : 'Не удалось открепить сотрудника от узла');
    } finally {
      setIsDetachingRecommendedAssignmentKey(null);
    }
  }, [loadTree, showErrorToast, showSuccessToast]);

  return {
    tree,
    recommendedTree,
    isLoading,
    error,
    recommendedError,
    canCreateRootUnit,
    visibleUnitIds,
    unitOptions,
    memberUnitByUserId,
    unassignedRecommendedMembers,
    unitDialogMode,
    activeUnit,
    unitName,
    setUnitName,
    isSavingUnit,
    createAssigneeSearch,
    setCreateAssigneeSearch,
    createAvailableUsers,
    selectedCreateUserId,
    setSelectedCreateUserId,
    isLoadingCreateUsers,
    isMemberDialogOpen,
    availableUsers,
    selectedUserId,
    setSelectedUserId,
    memberSearch,
    setMemberSearch,
    isLoadingUsers,
    isSavingMember,
    isAssigningRecommendedUserId,
    isDetachingRecommendedAssignmentKey,
    loadTree,
    openCreateRootDialog,
    openCreateChildDialog,
    openRenameDialog,
    closeUnitDialog,
    submitUnit,
    deactivateUnit,
    openMemberDialog,
    closeMemberDialog,
    submitMember,
    deleteMember,
    assignRecommendedMemberToUnit,
    detachRecommendedMemberFromUnit,
  };
};
