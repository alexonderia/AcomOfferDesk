import { fetchEmpty } from '../client';

export const resetUserPassword = (
  userId: string,
  payload: { new_password: string; password_confirmation: string },
) => fetchEmpty(
  `/api/v1/users/${encodeURIComponent(userId)}/password/reset`,
  { method: 'POST', body: JSON.stringify(payload) },
  'Не удалось сбросить пароль пользователя',
);
