import { fetchJson } from '../client';
import { normalizeUnitNode, type UnitNode } from './types';

export type UpdateUnitPayload = {
  name?: string;
  id_parent?: number;
};

type ResponseShape = {
  data: Parameters<typeof normalizeUnitNode>[0];
};

export const updateUnit = async (unitId: number, payload: UpdateUnitPayload): Promise<UnitNode> => {
  const response = await fetchJson<ResponseShape>(
    `/api/v1/units/${unitId}`,
    {
      method: 'PATCH',
      body: JSON.stringify(payload),
    },
    'Не удалось обновить подразделение'
  );

  return normalizeUnitNode(response.data);
};
