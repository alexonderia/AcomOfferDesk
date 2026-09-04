import { fetchJson } from '../client';

export type EmailVerificationResult = {
  detail: string;
  next_action?: string | null;
  redirect_url?: string | null;
};

export const requestEmailVerification = async (email: string): Promise<EmailVerificationResult> => {
  return fetchJson<EmailVerificationResult>(
    '/api/v1/auth/request-email-verification',
    {
      method: 'POST',
      body: JSON.stringify({ email })
    },
    'Не удалось отправить письмо для подтверждения email'
  );
};

export const verifyEmailToken = async (token: string): Promise<EmailVerificationResult> => {
  return fetchJson<EmailVerificationResult>(
    `/api/v1/auth/verify-email?token=${encodeURIComponent(token)}`,
    { method: 'GET' },
    'Не удалось подтвердить email',
    false
  );
};