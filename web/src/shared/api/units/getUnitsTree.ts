import { fetchJson } from '../client';
import { normalizeUnitNode, type UnitNode } from './types';

type ResponseShape = {
  data: {
    items: Array<Parameters<typeof normalizeUnitNode>[0]>;
  };
};

export const getUnitsTree = async (): Promise<UnitNode[]> => {
  const response = await fetchJson<ResponseShape>(
    '/api/v1/units/tree',
    { method: 'GET' },
    'Ошибка загрузки иерархии подразделений'
  );

  return response.data.items.map(normalizeUnitNode);
};
