import { fetchJson } from '../client';
import type { PlanMutationResult } from './types';

type CreateSubplanPayload = {
  parent_plan_id: number;
  name: string;
  period_start?: string;
  period_end?: string;
  child_user_id?: string;
  plan_amount: number;
};

type PlanMutationResponse = {
  data: PlanMutationResult;
};

export const createSubplan = async (payload: CreateSubplanPayload): Promise<PlanMutationResult> => {
  const response = await fetchJson<PlanMutationResponse>(
    '/api/v1/plans/subplan',
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
    'Не удалось создать подплан'
  );
  return response.data;
};
