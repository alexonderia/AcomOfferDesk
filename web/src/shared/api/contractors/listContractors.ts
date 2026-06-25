import { fetchJson } from '../client';
import { normalizeUserActions, type UserActions } from '../mappers';
import type { ContractorRootUnitsResult } from './getContractorRootUnits';

export type ContractorListItem = {
  userId: string;
  maxUserId: string | null;
  roleId: number;
  status: string;
  fullName: string | null;
  phone: string | null;
  mail: string | null;
  companyName: string | null;
  inn: string | null;
  companyPhone: string | null;
  companyMail: string | null;
  address: string | null;
  note: string | null;
  createdAt: string | null;
  updatedAt: string | null;
  registrationSource: string | null;
  actions: UserActions;
  rootUnits: ContractorRootUnitsResult | null;
};

export type ContractorListQuery = {
  search?: string;
  status?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
};

export type ContractorListResult = {
  items: ContractorListItem[];
  total: number;
  limit: number;
  offset: number;
};

type ContractorListItemPayload = {
  user_id: string;
  max_user_id?: string | null;
  role_id: number;
  status: string;
  full_name?: string | null;
  phone?: string | null;
  mail?: string | null;
  company_name?: string | null;
  inn?: string | null;
  company_phone?: string | null;
  company_mail?: string | null;
  address?: string | null;
  note?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  registration_source?: string | null;
  actions?: {
    can_view_profile?: boolean;
    can_update_status?: boolean;
    can_manage_contractor_unit_bindings?: boolean;
    can_manage_manual_contractor?: boolean;
  };
  root_unit_bindings?: {
    contractor_user_id: string;
    can_manage?: boolean;
    items?: Array<{
      unit_id: number;
      unit_name: string;
      is_bound: boolean;
      can_manage?: boolean;
    }>;
  } | null;
};

type ContractorListResponse = {
  data: {
    items: ContractorListItemPayload[];
    total?: number;
    limit?: number;
    offset?: number;
  };
};

const mapItem = (payload: ContractorListItemPayload): ContractorListItem => ({
  userId: payload.user_id,
  maxUserId: payload.max_user_id ?? null,
  roleId: payload.role_id,
  status: payload.status,
  fullName: payload.full_name ?? null,
  phone: payload.phone ?? null,
  mail: payload.mail ?? null,
  companyName: payload.company_name ?? null,
  inn: payload.inn ?? null,
  companyPhone: payload.company_phone ?? null,
  companyMail: payload.company_mail ?? null,
  address: payload.address ?? null,
  note: payload.note ?? null,
  createdAt: payload.created_at ?? null,
  updatedAt: payload.updated_at ?? null,
  registrationSource: payload.registration_source ?? null,
  actions: normalizeUserActions(payload.actions),
  rootUnits: payload.root_unit_bindings
    ? {
        contractorUserId: payload.root_unit_bindings.contractor_user_id,
        canManage: Boolean(payload.root_unit_bindings.can_manage),
        items: (payload.root_unit_bindings.items ?? []).map((item) => ({
          unitId: item.unit_id,
          unitName: item.unit_name,
          isBound: Boolean(item.is_bound),
          canManage: Boolean(item.can_manage),
        })),
      }
    : null,
});

const buildQueryString = (query: ContractorListQuery = {}) => {
  const params = new URLSearchParams();
  if (query.search?.trim()) {
    params.set('search', query.search.trim());
  }
  if (query.status?.trim()) {
    params.set('status', query.status.trim());
  }
  if (query.sortBy?.trim()) {
    params.set('sort_by', query.sortBy.trim());
  }
  if (query.sortOrder?.trim()) {
    params.set('sort_order', query.sortOrder.trim());
  }
  if (typeof query.limit === 'number') {
    params.set('limit', String(query.limit));
  }
  if (typeof query.offset === 'number') {
    params.set('offset', String(query.offset));
  }
  const search = params.toString();
  return search ? `?${search}` : '';
};

export const listContractorsTable = async (query: ContractorListQuery = {}): Promise<ContractorListResult> => {
  const response = await fetchJson<ContractorListResponse>(
    `/api/v1/contractors${buildQueryString(query)}`,
    { method: 'GET' },
    'Не удалось загрузить список контрагентов'
  );

  return {
    items: response.data.items.map(mapItem),
    total: response.data.total ?? response.data.items.length,
    limit: response.data.limit ?? query.limit ?? response.data.items.length,
    offset: response.data.offset ?? query.offset ?? 0,
  };
};

export const listContractors = async (): Promise<ContractorListItem[]> => (await listContractorsTable()).items;
