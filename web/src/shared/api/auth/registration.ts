import { fetchJson } from '../client';

export type RegistrationInspectResponse = {
  data: {
    status: 'ok' | 'invalid' | 'expired' | 'consumed' | 'in_progress' | string;
    email?: string | null;
    role_id?: number | null;
    expires_at?: string | null;
    login?: string | null;
    full_name?: string | null;
    phone?: string | null;
    company_name?: string | null;
    inn?: string | null;
    company_phone?: string | null;
  };
};

export type RegistrationSubmitPayload = {
  token: string;
  login: string;
  password: string;
  password_confirmation: string;
  email: string;
  full_name: string;
  phone: string;
  company_name: string;
  inn: string;
  company_phone: string;
  company_mail?: string;
  address?: string;
  note?: string;
};

export type RegistrationSubmitResponse = {
  data: {
    user_id: string;
    status: string;
    email: string;
  };
  detail: string;
};

export const inspectRegistrationInvitation = async (token: string): Promise<RegistrationInspectResponse> =>
  fetchJson<RegistrationInspectResponse>(
    `/api/v1/registration/invitations/${encodeURIComponent(token)}`,
    { method: 'GET', credentials: 'omit' },
    'Не удалось проверить ссылку регистрации',
    false,
  );

export const submitRegistration = async (
  payload: RegistrationSubmitPayload,
): Promise<RegistrationSubmitResponse> =>
  fetchJson<RegistrationSubmitResponse>(
    '/api/v1/registration/submit',
    {
      method: 'POST',
      credentials: 'omit',
      body: JSON.stringify(payload),
    },
    'Не удалось завершить регистрацию',
    false,
  );
