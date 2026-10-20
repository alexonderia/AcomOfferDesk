import { fetchJson } from '../client';
import { normalizeAvailableUnitUser, type AvailableUnitUser } from './types';

type ResponseShape = {
  data: {
    items: Array<Parameters<typeof normalizeAvailableUnitUser>[0]>;
  };
};

export const getAvailableUsersForUnit = async (
  unitId?: number,
  search?: string
): Promise<AvailableUnitUser[]> => {
  const params = new URLSearchParams();
  if (typeof unitId === 'number') {
    params.set('unit_id', String(unitId));
  }
  const normalizedSearch = search?.trim();
  if (normalizedSearch) {
    params.set('search', normalizedSearch);
  }

  const query = params.toString();

  const response = await fetchJson<ResponseShape>(
    query ? `/api/v1/units/available-users?${query}` : '/api/v1/units/available-users',
    { method: 'GET' },
    'Не удалось загрузить список доступных участников'
  );

  return response.data.items.map(normalizeAvailableUnitUser);
};
