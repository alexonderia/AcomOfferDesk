import { fetchJson } from '../client';
import type { PlanDelegateCandidate } from './types';

type DelegateCandidatesResponse = {
  data: {
    parent_plan_id: number;
    items: PlanDelegateCandidate[];
  };
};

export const getPlanDelegateCandidates = async (parentPlanId: number): Promise<PlanDelegateCandidate[]> => {
  const response = await fetchJson<DelegateCandidatesResponse>(
    `/api/v1/plans/delegate-candidates?parent_plan_id=${encodeURIComponent(String(parentPlanId))}`,
    { method: 'GET' },
    'Не удалось загрузить список подчиненных для делегирования'
  );
  return response.data.items;
};
