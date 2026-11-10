import { useEffect, useState } from 'react';
import type { UnitNode } from '@shared/api/units';
import { getEmployeeProfile, type EmployeeProfile } from '@shared/api/users/getEmployeeProfile';
import { getUserHierarchy, type UserHierarchy } from '@shared/api/users/getUserHierarchy';
import { getUserHierarchyUnitsTree } from '@shared/api/users/getUserHierarchyUnitsTree';

export const useHierarchyEmployeeCard = (userId: string) => {
  const [profile, setProfile] = useState<EmployeeProfile | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [hierarchy, setHierarchy] = useState<UserHierarchy | null>(null);
  const [unitsTree, setUnitsTree] = useState<UnitNode[]>([]);
  const [hierarchyError, setHierarchyError] = useState<string | null>(null);
  const [isLoadingHierarchy, setIsLoadingHierarchy] = useState(true);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    const { signal } = controller;
    setProfile(null);
    setError(null);
    setHierarchy(null);
    setUnitsTree([]);
    setHierarchyError(null);
    setIsLoadingHierarchy(true);
    void getEmployeeProfile(userId, signal)
      .then((data) => { if (!signal.aborted) setProfile(data); })
      .catch((cause: unknown) => {
        if (!signal.aborted) setError(cause instanceof Error ? cause.message : 'Не удалось загрузить карточку сотрудника');
      });
    void Promise.all([getUserHierarchy(userId, signal), getUserHierarchyUnitsTree(userId, signal)])
      .then(([data, tree]) => {
        if (!signal.aborted) { setHierarchy(data); setUnitsTree(tree); }
      })
      .catch((cause: unknown) => {
        if (!signal.aborted) setHierarchyError(cause instanceof Error ? cause.message : 'Не удалось загрузить иерархию сотрудника');
      })
      .finally(() => { if (!signal.aborted) setIsLoadingHierarchy(false); });
    return () => controller.abort();
  }, [userId, attempt]);

  return { profile, error, hierarchy, unitsTree, hierarchyError, isLoadingHierarchy,
    retry: () => setAttempt((value) => value + 1) };
};
