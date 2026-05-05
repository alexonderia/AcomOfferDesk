import { fetchJson } from '../client';
import type { PlanMutationResult } from './types';

type DelegatePlanPayload = {
  parent_plan_id: number;
  child_user_id: string;
  child_period_start?: string;
  child_plan_amount: number;
};

type PlanMutationResponse = {
  data: PlanMutationResult;
};

export const delegatePlan = async (payload: DelegatePlanPayload): Promise<PlanMutationResult> => {
  const response = await fetchJson<PlanMutationResponse>(
    '/api/v1/plans/delegate',
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
    'Не удалось делегировать план'
  );
  return response.data;
};
