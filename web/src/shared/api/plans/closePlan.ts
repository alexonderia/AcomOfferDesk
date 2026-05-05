import { fetchJson } from '../client';
import type { PlanMutationResult } from './types';

type PlanMutationResponse = {
  data: PlanMutationResult;
};

export const closePlan = async (planId: number): Promise<PlanMutationResult> => {
  const response = await fetchJson<PlanMutationResponse>(
    `/api/v1/plans/${planId}/close`,
    {
      method: 'POST',
    },
    'Не удалось закрыть план'
  );
  return response.data;
};
