import { normalizeUnitNode, type UnitNode } from '@shared/api/units/types';
import { fetchJson } from '../client';

type ResponseShape = {
  data: {
    items: Array<Parameters<typeof normalizeUnitNode>[0]>;
  };
};

export const getUserHierarchyUnitsTree = async (userId: string): Promise<UnitNode[]> => {
  const response = await fetchJson<ResponseShape>(
    `/api/v1/users/${userId}/hierarchy/units-tree`,
    { method: 'GET' },
    'Ошибка загрузки иерархии объединений сотрудника',
  );

  return response.data.items.map(normalizeUnitNode);
};
