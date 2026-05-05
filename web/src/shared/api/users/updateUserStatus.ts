import { fetchJson } from '../client';

type UpdateUserStatusPayload = {
  user_status: 'review' | 'active' | 'inactive' | 'blacklist';
};

type UpdateUserStatusResponse = {
  data: {
    user_id: string;
    user_status: string;
  };
};

export const updateUserStatus = async (
  userId: string,
  payload: UpdateUserStatusPayload
): Promise<UpdateUserStatusResponse> =>
  fetchJson<UpdateUserStatusResponse>(
    `/api/v1/users/${encodeURIComponent(userId)}/status`,
    {
      method: 'PATCH',
      body: JSON.stringify(payload)
    },
    'Не удалось обновить статус пользователя'
  );
