import { fetchJson } from '../client';
import type { UserListItem } from './getUsers';
import { ROLE } from '@shared/constants/roles';
import { normalizeUserActions } from '../mappers';

type EconomistRow = {
  user_id: string;
  status: string;
  full_name?: string | null;
  phone?: string | null;
  mail?: string | null;
  actions?: {
    can_update_status?: boolean;
    can_update_role?: boolean;
  };
};

type EconomistListResponse = {
  data: {
    items: EconomistRow[];
    permissions?: string[];
  };
};

export type GetEconomistsResult = {
  items: UserListItem[];
  permissions: string[];
};

export const getEconomists = async (): Promise<GetEconomistsResult> => {
  const response = await fetchJson<EconomistListResponse>(
    '/api/v1/users/economists',
    { method: 'GET' },
    'Ошибка загрузки экономистов'
  );

  return {
    items: response.data.items.map((item) => ({
      user_id: item.user_id,
      role_id: ROLE.ECONOMIST,
      id_parent: null,
      status: item.status,
      full_name: item.full_name ?? null,
      phone: item.phone ?? null,
      mail: item.mail ?? null,
      company_name: null,
      inn: null,
      company_phone: null,
      company_mail: null,
      address: null,
      note: null,
      actions: normalizeUserActions(item.actions)
    })),
    permissions: response.data.permissions ?? []
  };
};
