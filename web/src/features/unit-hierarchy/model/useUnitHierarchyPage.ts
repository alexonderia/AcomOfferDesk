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

const flattenUnitIds = (nodes: UnitNode[]): number[] =>
  nodes.flatMap((node) => [node.unit_id, ...flattenUnitIds(node.children)]);

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
  const [isLoadingUsers, setIsLoadingUsers] = useState(false);
  const [isSavingMember, setIsSavingMember] = useState(false);

  const canCreateRootUnit = hasPermission(session, 'units.create') && session?.roleId === ROLE.SUPERADMIN;
  const visibleUnitIds = useMemo(() => new Set(flattenUnitIds(tree)), [tree]);

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

  useEffect(() => {
    if (!isMemberDialogOpen || !activeUnit) {
      return;
    }
    void loadAvailableUsers(activeUnit.unit_id, deferredMemberSearch);
  }, [activeUnit, deferredMemberSearch, isMemberDialogOpen, loadAvailableUsers]);

  const closeUnitDialog = useCallback(() => {
    setUnitDialogMode(null);
    setActiveUnit(null);
    setUnitName('');
  }, []);

  const openCreateRootDialog = useCallback(() => {
    setUnitDialogMode('create-root');
    setActiveUnit(null);
    setUnitName('');
  }, []);

  const openCreateChildDialog = useCallback((unit: UnitNode) => {
    setUnitDialogMode('create-child');
    setActiveUnit(unit);
    setUnitName('');
  }, []);

  const openRenameDialog = useCallback((unit: UnitNode) => {
    setUnitDialogMode('rename');
    setActiveUnit(unit);
    setUnitName(unit.name);
  }, []);

  const submitUnit = useCallback(async () => {
    const normalizedName = unitName.trim();
    if (!normalizedName) {
      showErrorToast('Название подразделения обязательно');
      return;
    }

    setIsSavingUnit(true);
    try {
      if (unitDialogMode === 'rename' && activeUnit) {
        await updateUnit(activeUnit.unit_id, { name: normalizedName });
        showSuccessToast('Название подразделения обновлено');
      } else {
        await createUnit({
          name: normalizedName,
          id_parent: unitDialogMode === 'create-child' && activeUnit ? activeUnit.unit_id : undefined,
        });
        showSuccessToast('Подразделение создано');
      }
      closeUnitDialog();
      await loadTree();
    } catch (submitError) {
      showErrorToast(submitError instanceof Error ? submitError.message : 'Не удалось сохранить подразделение');
    } finally {
      setIsSavingUnit(false);
    }
  }, [activeUnit, closeUnitDialog, loadTree, showErrorToast, showSuccessToast, unitDialogMode, unitName]);

  const deactivateUnit = useCallback(async (unit: UnitNode) => {
    if (!window.confirm(`Деактивировать подразделение «${unit.name}»?`)) {
      return;
    }

    try {
      await updateUnit(unit.unit_id, { is_active: false });
      showSuccessToast('Подразделение деактивировано');
      await loadTree();
    } catch (deactivateError) {
      showErrorToast(deactivateError instanceof Error ? deactivateError.message : 'Не удалось деактивировать подразделение');
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
      showErrorToast('Выберите пользователя');
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
    if (!window.confirm(`Удалить участника «${member.full_name ?? member.user_id}» из подразделения «${unit.name}»?`)) {
      return;
    }

    try {
      await removeUnitMember(unit.unit_id, member.user_id);
      showSuccessToast('Участник удален');
      await loadTree();
    } catch (deleteError) {
      showErrorToast(deleteError instanceof Error ? deleteError.message : 'Не удалось удалить участника');
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
    unitDialogMode,
    activeUnit,
    unitName,
    setUnitName,
    isSavingUnit,
    isMemberDialogOpen,
    availableUsers,
    selectedUserId,
    setSelectedUserId,
    memberSearch,
    setMemberSearch,
    isLoadingUsers,
    isSavingMember,
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
  };
};
