import { fetchJson } from '../client';
import type { PlanMutationResult } from './types';

type UpdatePlanPayload = {
  plan_amount?: number;
  name?: string;
  period_end?: string;
  status?: string;
};

type PlanMutationResponse = {
  data: PlanMutationResult;
};

export const updatePlan = async (planId: number, payload: UpdatePlanPayload): Promise<PlanMutationResult> => {
  const response = await fetchJson<PlanMutationResponse>(
    `/api/v1/plans/${planId}`,
    {
      method: 'PATCH',
      body: JSON.stringify(payload),
    },
    'Не удалось обновить план'
  );
  return response.data;
};
