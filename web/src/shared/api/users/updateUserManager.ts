import { fetchJson } from '../client';

type UpdateUserManagerPayload = {
  manager_user_id: string;
};

type UpdateUserManagerResponse = {
  data: {
    user_id: string;
    manager_user_id: string;
  };
};

export const updateUserManager = async (
  userId: string,
  payload: UpdateUserManagerPayload
): Promise<UpdateUserManagerResponse> =>
  fetchJson<UpdateUserManagerResponse>(
    `/api/v1/users/${encodeURIComponent(userId)}/manager`,
    {
      method: 'PATCH',
      body: JSON.stringify(payload)
    },
    'Не удалось обновить руководителя пользователя'
  );
