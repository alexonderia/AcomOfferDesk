import { fetchJson } from '../client';
import type { PlanMutationResult } from './types';

type CreateRootPlanPayload = {
  period?: string;
  period_start?: string;
  period_end?: string;
  name: string;
  plan_amount: number;
};

type PlanMutationResponse = {
  data: PlanMutationResult;
};

export const createRootPlan = async (payload: CreateRootPlanPayload): Promise<PlanMutationResult> => {
  const response = await fetchJson<PlanMutationResponse>(
    '/api/v1/plans/root',
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
    'Не удалось создать корневой план'
  );
  return response.data;
};
