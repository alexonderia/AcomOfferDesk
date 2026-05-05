import { fetchJson } from '../client';
import type { PlanDashboardResult } from './types';

type PlanDashboardResponse = {
  data: PlanDashboardResult;
};

type GetPlanDashboardParams = {
  period?: string;
  dateFrom?: string;
  dateTo?: string;
};

export const getPlanDashboard = async ({
  period,
  dateFrom,
  dateTo,
}: GetPlanDashboardParams): Promise<PlanDashboardResult> => {
  const query = dateFrom && dateTo
    ? `date_from=${encodeURIComponent(dateFrom)}&date_to=${encodeURIComponent(dateTo)}`
    : `period=${encodeURIComponent(period ?? '')}`;
  const response = await fetchJson<PlanDashboardResponse>(
    `/api/v1/plans?${query}`,
    { method: 'GET' },
    'Не удалось загрузить вкладку плана'
  );
  return response.data;
};
