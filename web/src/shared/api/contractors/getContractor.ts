import { fetchJson } from '../client';
import { normalizeUserActions, type UserActions } from '../mappers';

export type ContractorProfile = {
  userId: string;
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
  actions: UserActions;
};

type ContractorProfilePayload = {
  user_id: string;
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
  actions?: {
    can_view_profile?: boolean;
    can_update_status?: boolean;
  };
};

type ContractorProfileResponse = {
  data: ContractorProfilePayload;
};

const mapProfile = (payload: ContractorProfilePayload): ContractorProfile => ({
  userId: payload.user_id,
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
  actions: normalizeUserActions(payload.actions),
});

export const getContractor = async (contractorId: string): Promise<ContractorProfile> => {
  const response = await fetchJson<ContractorProfileResponse>(
    `/api/v1/contractors/${encodeURIComponent(contractorId)}`,
    { method: 'GET' },
    'Не удалось загрузить данные контрагента'
  );
  return mapProfile(response.data);
};
