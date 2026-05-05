import { fetchJson } from '../client';
import type { PlanOption } from './types';

type PlanOptionsResponse = {
  data: {
    period: string;
    items: PlanOption[];
  };
};

type GetPlanOptionsParams = {
  period?: string;
  ownerUserId?: string;
};

export const getPlanOptions = async ({ period, ownerUserId }: GetPlanOptionsParams): Promise<PlanOption[]> => {
  const query = ownerUserId
    ? `owner_user_id=${encodeURIComponent(ownerUserId)}`
    : `period=${encodeURIComponent(period ?? '')}`;
  const response = await fetchJson<PlanOptionsResponse>(
    `/api/v1/plans/options?${query}`,
    { method: 'GET' },
    'Не удалось загрузить список планов'
  );
  return response.data.items;
};
