import { fetchEmpty, fetchJson } from '../client';

export type AuthSessionResponse = {
  data: {
    user_id: string;
    login: string;
    role_id: number;
    role: string;
    status: string;
    auth_provider?: string;
    business_access?: boolean;
    onboarding_state?: string | null;
    permissions?: string[];
  };
};

export const getWebSession = async (): Promise<AuthSessionResponse> =>
  fetchJson<AuthSessionResponse>(
    '/api/v1/auth/session',
    { method: 'GET' },
    'Не удалось проверить сессию',
    false
  );

export const issueCsrfToken = async (): Promise<void> => {
  await fetchJson<{ csrf_token: string }>(
    '/api/v1/auth/csrf',
    { method: 'GET' },
    'Не удалось подготовить защищённую сессию',
    false
  );
};

export const refreshWebSession = async (): Promise<AuthSessionResponse> =>
  fetchJson<AuthSessionResponse>(
    '/api/v1/auth/refresh',
    {
      method: 'POST'
    },
    'Не удалось восстановить сессию',
    false
  );

export const logoutWebSession = async (): Promise<void> =>
  fetchEmpty(
    '/api/v1/auth/logout',
    {
      method: 'POST'
    },
    'Не удалось завершить сессию',
    false
  );

export const logoutIamBrowserSession = async (): Promise<void> =>
  fetchEmpty(
    '/iam/logout',
    {
      method: 'POST',
    },
    'Не удалось завершить сессию авторизации',
    false,
  );
