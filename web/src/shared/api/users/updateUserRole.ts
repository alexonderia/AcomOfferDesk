import { fetchJson } from '../client';

type UpdateUserRolePayload = {
  role_id: number;
};

type UpdateUserRoleResponse = {
  data: {
    user_id: string;
    role_id: number;
  };
};

export const updateUserRole = async (
  userId: string,
  payload: UpdateUserRolePayload
): Promise<UpdateUserRoleResponse> =>
  fetchJson<UpdateUserRoleResponse>(
    `/api/v1/users/${encodeURIComponent(userId)}/role`,
    {
      method: 'PATCH',
      body: JSON.stringify(payload)
    },
    'Не удалось обновить роль пользователя'
  );
