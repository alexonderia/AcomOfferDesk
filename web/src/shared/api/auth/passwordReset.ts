import { fetchJson } from '../client';


type PasswordResetResponse = {
  detail: string;
};


export const requestPasswordReset = async (login: string): Promise<string> => {
  const response = await fetchJson<PasswordResetResponse>(
    '/api/v1/auth/password-reset/request',
    {
      method: 'POST',
      credentials: 'omit',
      body: JSON.stringify({ login: login.trim() }),
    },
    'Не удалось запросить сброс пароля',
    false,
  );
  return response.detail;
};
