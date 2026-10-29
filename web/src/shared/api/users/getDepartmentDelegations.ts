import { fetchJson } from '../client';

export type DepartmentDelegationAccess = {
  code: string;
  permissionCode: string;
  group: string;
  label: string;
  enabled: boolean;
  grantedViaRole: boolean;
  grantedIndividually: boolean;
};

export type UserDepartmentDelegations = {
  userId: string;
  roleId: number;
  fullName: string | null;
  canManage: boolean;
  accesses: DepartmentDelegationAccess[];
  tokenRefreshRequired: boolean;
  warning: string | null;
};

type DepartmentDelegationAccessPayload = {
  code: string;
  permission_code: string;
  group: string;
  label: string;
  enabled: boolean;
  granted_via_role: boolean;
  granted_individually: boolean;
};

type UserDepartmentDelegationsPayload = {
  user_id: string;
  role_id: number;
  full_name?: string | null;
  can_manage: boolean;
  accesses: DepartmentDelegationAccessPayload[];
  token_refresh_required?: boolean;
  warning?: string | null;
};

type UserDepartmentDelegationsResponse = {
  data: UserDepartmentDelegationsPayload;
};

const mapDelegations = (payload: UserDepartmentDelegationsPayload): UserDepartmentDelegations => ({
  userId: payload.user_id,
  roleId: payload.role_id,
  fullName: payload.full_name ?? null,
  canManage: payload.can_manage,
  accesses: payload.accesses.map((item) => ({
    code: item.code,
    permissionCode: item.permission_code,
    group: item.group,
    label: item.label,
    enabled: item.enabled,
    grantedViaRole: item.granted_via_role,
    grantedIndividually: item.granted_individually,
  })),
  tokenRefreshRequired: Boolean(payload.token_refresh_required),
  warning: payload.warning ?? null,
});

export const getDepartmentDelegations = async (userId: string): Promise<UserDepartmentDelegations> => {
  const response = await fetchJson<UserDepartmentDelegationsResponse>(
    `/api/v1/users/${userId}/delegations/department`,
    { method: 'GET' },
    'Failed to load department delegations'
  );
  return mapDelegations(response.data);
};

export const updateDepartmentDelegations = async (
  userId: string,
  accessCodes: string[]
): Promise<UserDepartmentDelegations> => {
  const response = await fetchJson<UserDepartmentDelegationsResponse>(
    `/api/v1/users/${userId}/delegations/department`,
    {
      method: 'PUT',
      body: JSON.stringify({ access_codes: accessCodes }),
    },
    'Failed to update department delegations'
  );
  return mapDelegations(response.data);
};
