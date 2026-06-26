import { fetchJson } from '../client';
import { normalizeAvailableUnitUser, type AvailableUnitUser } from './types';

type ResponseShape = {
  data: {
    items: Array<Parameters<typeof normalizeAvailableUnitUser>[0]>;
  };
};

export const getAvailableContractorsForUnit = async (
  unitId: number,
  search?: string
): Promise<AvailableUnitUser[]> => {
  const params = new URLSearchParams();
  const normalizedSearch = search?.trim();
  if (normalizedSearch) {
    params.set('search', normalizedSearch);
  }

  const query = params.toString();

  const response = await fetchJson<ResponseShape>(
    query
      ? `/api/v1/units/${unitId}/available-contractors?${query}`
      : `/api/v1/units/${unitId}/available-contractors`,
    { method: 'GET' },
    'Не удалось загрузить список контрагентов'
  );

  return response.data.items.map(normalizeAvailableUnitUser);
};
