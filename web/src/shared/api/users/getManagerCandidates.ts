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
  };
};

export type GetManagerCandidatesResult = {
  items: UserListItem[];
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
  units_count: 0,
  managers_count: 0,
  subordinates_count: 0,
  actions: normalizeUserActions(item.actions)
});

/** @deprecated Легаси: иерархия users.id_parent. На сайте не используется — только оргструктура (юниты). */
export const getManagerCandidates = async (
  targetRoleId: number,
  targetUserId?: string
): Promise<GetManagerCandidatesResult> => {
  const query = new URLSearchParams({ target_role_id: String(targetRoleId) });
  if (targetUserId?.trim()) {
    query.set('target_user_id', targetUserId.trim());
  }
  const response = await fetchJson<UserListResponse>(
    `/api/v1/users/manager-candidates?${query.toString()}`,
    { method: 'GET' },
    'Ошибка загрузки списка руководителей'
  );

  return {
    items: response.data.items.map(normalizeUserItem)
  };
};
