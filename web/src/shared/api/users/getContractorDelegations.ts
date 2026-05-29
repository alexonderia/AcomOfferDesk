import { fetchJson } from '../client';

export type ContractorDelegationAccess = {
  code: string;
  label: string;
  description: string;
  enabled: boolean;
};

export type UserContractorDelegations = {
  userId: string;
  roleId: number;
  fullName: string | null;
  canManage: boolean;
  accesses: ContractorDelegationAccess[];
  tokenRefreshRequired: boolean;
  warning: string | null;
};

type ContractorDelegationAccessPayload = {
  code: string;
  label: string;
  description: string;
  enabled: boolean;
};

type UserContractorDelegationsPayload = {
  user_id: string;
  role_id: number;
  full_name?: string | null;
  can_manage: boolean;
  accesses: ContractorDelegationAccessPayload[];
  token_refresh_required?: boolean;
  warning?: string | null;
};

type UserContractorDelegationsResponse = {
  data: UserContractorDelegationsPayload;
};

const mapDelegations = (payload: UserContractorDelegationsPayload): UserContractorDelegations => ({
  userId: payload.user_id,
  roleId: payload.role_id,
  fullName: payload.full_name ?? null,
  canManage: payload.can_manage,
  accesses: payload.accesses.map((item) => ({
    code: item.code,
    label: item.label,
    description: item.description,
    enabled: item.enabled,
  })),
  tokenRefreshRequired: Boolean(payload.token_refresh_required),
  warning: payload.warning ?? null,
});

export const getContractorDelegations = async (userId: string): Promise<UserContractorDelegations> => {
  const response = await fetchJson<UserContractorDelegationsResponse>(
    `/api/v1/users/${userId}/delegations/contractors`,
    { method: 'GET' },
    'Failed to load contractor delegations'
  );
  return mapDelegations(response.data);
};

export const updateContractorDelegations = async (
  userId: string,
  accessCodes: string[]
): Promise<UserContractorDelegations> => {
  const response = await fetchJson<UserContractorDelegationsResponse>(
    `/api/v1/users/${userId}/delegations/contractors`,
    {
      method: 'PUT',
      body: JSON.stringify({ access_codes: accessCodes }),
    },
    'Failed to update contractor delegations'
  );
  return mapDelegations(response.data);
};
