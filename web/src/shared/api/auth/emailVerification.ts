import { fetchJson } from '../client';

export const requestEmailVerification = async (email: string): Promise<{ detail: string }> => {
  return fetchJson<{ detail: string }>(
    '/api/v1/auth/request-email-verification',
    {
      method: 'POST',
      body: JSON.stringify({ email })
    },
    'Не удалось отправить письмо для подтверждения email'
  );
};

export const verifyEmailToken = async (token: string): Promise<{ detail: string }> => {
  return fetchJson<{ detail: string }>(
    `/api/v1/auth/verify-email?token=${encodeURIComponent(token)}`,
    { method: 'GET' },
    'Не удалось подтвердить email',
    false
  );
};