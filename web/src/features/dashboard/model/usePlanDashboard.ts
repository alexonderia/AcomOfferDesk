import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  closePlan,
  createRootPlan,
  createSubplan,
  delegatePlan,
  deletePlan,
  getPlanDashboard,
  getPlanDelegateCandidates,
  updatePlan,
  type PlanDashboardResult,
  type PlanDelegateCandidate,
} from '@shared/api/plans';

const getCurrentPeriod = () => {
  const now = new Date();
  const month = `${now.getMonth() + 1}`.padStart(2, '0');
  return `${now.getFullYear()}-${month}`;
};

const monthToStartDate = (period: string) => `${period}-01`;
const monthToEndDate = (period: string) => {
  const [yearString, monthString] = period.split('-');
  const year = Number.parseInt(yearString ?? '', 10);
  const month = Number.parseInt(monthString ?? '', 10);
  if (!Number.isFinite(year) || !Number.isFinite(month) || month < 1 || month > 12) {
    return `${period}-28`;
  }
  const day = new Date(year, month, 0).getDate();
  return `${period}-${String(day).padStart(2, '0')}`;
};

export const usePlanDashboard = () => {
  const [period, setPeriod] = useState<string>(getCurrentPeriod);
  const [dateFrom, setDateFrom] = useState<string>(() => monthToStartDate(getCurrentPeriod()));
  const [dateTo, setDateTo] = useState<string>(() => monthToEndDate(getCurrentPeriod()));
  const [data, setData] = useState<PlanDashboardResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isMutating, setIsMutating] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const loadDashboard = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const next = await getPlanDashboard({ period, dateFrom, dateTo });
      setData(next);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Не удалось загрузить план');
    } finally {
      setIsLoading(false);
    }
  }, [period, dateFrom, dateTo]);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  const withMutation = useCallback(async (action: () => Promise<void>) => {
    setIsMutating(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    try {
      await action();
      await loadDashboard();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Операция с планом не выполнена');
    } finally {
      setIsMutating(false);
    }
  }, [loadDashboard]);

  const createRoot = useCallback(async (
    name: string,
    planAmount: number,
    periodStart?: string,
    periodEnd?: string,
  ) => {
    await withMutation(async () => {
      await createRootPlan({
        period,
        period_start: periodStart ?? monthToStartDate(period),
        period_end: periodEnd,
        name,
        plan_amount: planAmount,
      });
      setSuccessMessage('Корневой план создан');
    });
  }, [period, withMutation]);

  const createSubplanNode = useCallback(async (parentPlanId: number, name: string, amount: number) => {
    await withMutation(async () => {
      await createSubplan({
        parent_plan_id: parentPlanId,
        name,
        period_start: undefined,
        plan_amount: amount,
      });
      setSuccessMessage('Подплан создан');
    });
  }, [withMutation]);

  const createSubplanNodeWithStart = useCallback(async (
    parentPlanId: number,
    name: string,
    amount: number,
    periodStart?: string,
    periodEnd?: string,
    childUserId?: string,
  ) => {
    await withMutation(async () => {
      await createSubplan({
        parent_plan_id: parentPlanId,
        name,
        period_start: periodStart,
        period_end: periodEnd,
        child_user_id: childUserId,
        plan_amount: amount,
      });
      setSuccessMessage('Подплан создан');
    });
  }, [withMutation]);

  const delegate = useCallback(async (
    parentPlanId: number,
    childUserId: string,
    childPlanAmount: number,
    childPeriodStart?: string
  ) => {
    await withMutation(async () => {
      await delegatePlan({
        parent_plan_id: parentPlanId,
        child_user_id: childUserId,
        child_period_start: childPeriodStart,
        child_plan_amount: childPlanAmount,
      });
      setSuccessMessage('План делегирован');
    });
  }, [withMutation]);

  const updatePlanNode = useCallback(async (
    planId: number,
    payload: { planAmount?: number; name?: string; periodEnd?: string },
  ) => {
    await withMutation(async () => {
      await updatePlan(planId, {
        plan_amount: payload.planAmount,
        name: payload.name,
        period_end: payload.periodEnd,
      });
      setSuccessMessage('План обновлен');
    });
  }, [withMutation]);

  const removeChildPlan = useCallback(async (planId: number) => {
    await withMutation(async () => {
      await deletePlan(planId);
      setSuccessMessage('План удален');
    });
  }, [withMutation]);

  const closePlanNode = useCallback(async (planId: number) => {
    await withMutation(async () => {
      await closePlan(planId);
      setSuccessMessage('План закрыт');
    });
  }, [withMutation]);

  const loadDelegateCandidates = useCallback(async (parentPlanId: number): Promise<PlanDelegateCandidate[]> => {
    return await getPlanDelegateCandidates(parentPlanId);
  }, []);

  const summary = useMemo(() => data?.summary ?? null, [data]);
  const requestStats = useMemo(() => data?.request_stats ?? null, [data]);

  return {
    period,
    setPeriod,
    dateFrom,
    dateTo,
    setDateFrom,
    setDateTo,
    data,
    tree: data?.tree ?? null,
    trees: data?.trees ?? (data?.tree ? [data.tree] : []),
    summary,
    requestStats,
    canCreateRootPlan: data?.can_create_root_plan ?? false,
    rootPlanExists: data?.root_plan_exists ?? false,
    isLoading,
    isMutating,
    errorMessage,
    successMessage,
    setSuccessMessage,
    reload: loadDashboard,
    createRoot,
    createSubplanNode,
    createSubplanNodeWithStart,
    delegate,
    updatePlanNode,
    removeChildPlan,
    closePlanNode,
    loadDelegateCandidates,
  };
};
