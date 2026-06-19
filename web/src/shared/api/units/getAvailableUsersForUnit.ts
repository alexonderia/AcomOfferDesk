import { fetchJson } from '../client';
import { normalizeAvailableUnitUser, type AvailableUnitUser } from './types';

type ResponseShape = {
  data: {
    items: Array<Parameters<typeof normalizeAvailableUnitUser>[0]>;
  };
};

export const getAvailableUsersForUnit = async (
  unitId: number,
  search?: string
): Promise<AvailableUnitUser[]> => {
  const params = new URLSearchParams({ unit_id: String(unitId) });
  const normalizedSearch = search?.trim();
  if (normalizedSearch) {
    params.set('search', normalizedSearch);
  }

  const response = await fetchJson<ResponseShape>(
    `/api/v1/units/available-users?${params.toString()}`,
    { method: 'GET' },
    'Не удалось загрузить список доступных участников'
  );

  return response.data.items.map(normalizeAvailableUnitUser);
};
