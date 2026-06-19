import { fetchJson } from '../client';
import { normalizeUnitNode, type UnitNode } from './types';

export type CreateUnitPayload = {
  name: string;
  id_parent?: number;
};

type ResponseShape = {
  data: Parameters<typeof normalizeUnitNode>[0];
};

export const createUnit = async (payload: CreateUnitPayload): Promise<UnitNode> => {
  const response = await fetchJson<ResponseShape>(
    '/api/v1/units',
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
    'Не удалось создать подразделение'
  );

  return normalizeUnitNode(response.data);
};
