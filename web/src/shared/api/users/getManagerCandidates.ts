import { fetchJson } from '../client';
import type { UserListItem } from '@entities/user';
import { normalizeUserActions } from '../mappers';

type UsersRow = {
  user_id?: string;
  role_id?: number;
  id_parent?: string | null;
  status?: string;
  full_name?: string | null;
  phone?: string | null;
  mail?: string | null;
  actions?: {
    can_update_status?: boolean;
    can_update_role?: boolean;
    can_update_manager?: boolean;
  };
};

type UserListResponse = {
  data: {
    items: UsersRow[];
    permissions?: string[];
  };
};

export type GetManagerCandidatesResult = {
  items: UserListItem[];
  permissions: string[];
};

const normalizeUserItem = (item: UsersRow): UserListItem => ({
  user_id: item.user_id ?? '',
  role_id: item.role_id ?? 0,
  id_parent: item.id_parent ?? null,
  status: item.status ?? 'review',
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
});

export const getManagerCandidates = async (targetRoleId: number): Promise<GetManagerCandidatesResult> => {
  const response = await fetchJson<UserListResponse>(
    `/api/v1/users/manager-candidates?target_role_id=${targetRoleId}`,
    { method: 'GET' },
    'Ошибка загрузки списка руководителей'
  );

  return {
    items: response.data.items.map(normalizeUserItem),
    permissions: response.data.permissions ?? []
  };
};
