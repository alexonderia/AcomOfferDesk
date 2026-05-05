import { fetchJson } from '../client';
import type { UserListItem } from '@entities/user';
import { normalizeUserActions } from '../mappers';

export type { UserListItem } from '@entities/user';

type UsersRow = {
  id?: string;
  user_id?: string;
  id_role?: number;
  role_id?: number;
  id_parent?: string | null;
  status?: string;
  full_name?: string | null;
  phone?: string | null;
  mail?: string | null;
  company_name?: string | null;
  inn?: string | null;
  company_phone?: string | null;
  company_mail?: string | null;
  address?: string | null;
  note?: string | null;
  actions?: {
    can_view_profile?: boolean;
    can_update_status?: boolean;
    can_update_role?: boolean;
    can_update_manager?: boolean;
    can_manage_subordinate_unavailability?: boolean;
    can_manage_manual_contractor?: boolean;
  };
  users?: {
    id?: string;
    id_role?: number;
    role_id?: number;
    status?: string;
  };
  profiles?: {
    id?: string;
    full_name?: string | null;
    phone?: string | null;
    mail?: string | null;
  };
  company_contacts?: {
    id?: string;
    company_name?: string | null;
    inn?: string | null;
    phone?: string | null;
    mail?: string | null;
    address?: string | null;
    note?: string | null;
  };
};

type UserListResponse = {
  data: {
    items: UsersRow[];
    permissions?: string[];
  };
};

export type GetUsersResult = {
  items: UserListItem[];
  permissions: string[];
};

const normalizeUserItem = (item: UsersRow): UserListItem => {
  const users = item.users;
  const profile = item.profiles;
  const company = item.company_contacts;
  const userId = item.user_id ?? users?.id ?? item.id ?? profile?.id ?? company?.id ?? '';
  const roleId = item.role_id ?? users?.role_id ?? item.id_role ?? users?.id_role ?? 0;
  const companyPhone = item.company_phone ?? company?.phone ?? null;
  const companyMail = item.company_mail ?? company?.mail ?? null;

  return {
    user_id: userId,
    role_id: roleId,
    id_parent: item.id_parent ?? null,
    status: item.status ?? users?.status ?? 'review',
    full_name: item.full_name ?? profile?.full_name ?? null,
    phone: item.phone ?? profile?.phone ?? null,
    mail: item.mail ?? profile?.mail ?? null,
    company_name: item.company_name ?? company?.company_name ?? null,
    inn: item.inn ?? company?.inn ?? null,
    company_phone: companyPhone,
    company_mail: companyMail,
    address: item.address ?? company?.address ?? null,
    note: item.note ?? company?.note ?? null,
    actions: normalizeUserActions(item.actions)
  };
};

export const getUsers = async (roleId?: number): Promise<GetUsersResult> => {
  const search = typeof roleId === 'number' ? `?role_id=${roleId}` : '';
  const response = await fetchJson<UserListResponse>(
    `/api/v1/users${search}`,
    { method: 'GET' },
    'Ошибка загрузки пользователей'
  );

  return {
    items: response.data.items.map(normalizeUserItem),
    permissions: response.data.permissions ?? []
  };
};
