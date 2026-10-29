import { fetchJson } from '../client';
import type { UnitMember } from './types';

type ResponseShape = {
  data: UnitMember;
};

export const addUnitContractor = async (unitId: number, userId: string): Promise<UnitMember> => {
  const response = await fetchJson<ResponseShape>(
    `/api/v1/units/${unitId}/contractors`,
    {
      method: 'POST',
      body: JSON.stringify({ user_id: userId }),
    },
    'Не удалось привязать контрагента'
  );

  return {
    user_id: response.data.user_id ?? '',
    full_name: response.data.full_name ?? null,
    role_id: response.data.role_id ?? 0,
    role_name: response.data.role_name ?? '',
    status: response.data.status ?? 'review',
    id_parent_user: response.data.id_parent_user ?? null,
  };
};
