// LEGACY_TELEGRAM: API methods are kept for rollback and are not used in active routes.
import { fetchJson } from '../client';

export type RequestTgEmailVerificationPayload = {
  token: string;
  mail: string;
};

export type CheckTgLoginAvailabilityResponse = {
  available: boolean;
  detail: string;
};

export type CompleteTgRegistrationPayload = {
  token: string;
  login: string;
  password: string;
  password_confirm: string;
  full_name: string;
  phone: string;
  mail: string;
  company_name: string;
  inn: string;
  company_phone: string;
  company_mail: string;
  address: string;
  note: string;
};

export type CompleteTgRegistrationResponse = {
  data: {
    user_id: string;
    status: string;
    tg_user_id: number;
  };
  _links: {
    self: { href: string; method: string };
    available_action?: { href: string; method: string };
  };
};

export const requestTgEmailVerification = async (payload: RequestTgEmailVerificationPayload): Promise<{ detail: string }> => {
  return fetchJson<{ detail: string }>(
    '/api/v1/tg/register/request-email-verification/',
    {
      method: 'POST',
      body: JSON.stringify(payload)
    },
    'Ошибка отправки письма подтверждения',
    false
  );
};

export const checkTgLoginAvailability = async (
  token: string,
  login: string
): Promise<CheckTgLoginAvailabilityResponse> => {
  const query = new URLSearchParams({ token, login }).toString();
  return fetchJson<CheckTgLoginAvailabilityResponse>(
    `/api/v1/tg/register/login-availability/?${query}`,
    { method: 'GET' },
    'Ошибка проверки логина',
    false
  );
};

export const completeTgRegistration = async (
  payload: CompleteTgRegistrationPayload
): Promise<CompleteTgRegistrationResponse> => {
  return fetchJson<CompleteTgRegistrationResponse>(
    '/api/v1/tg/register/complete/',
    {
      method: 'POST',
      body: JSON.stringify(payload)
    },
    'Ошибка регистрации',
    false
  );
};
