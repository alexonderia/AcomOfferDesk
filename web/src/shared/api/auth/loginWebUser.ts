import { apiFetch, fetchEmpty, fetchJson } from '../client';

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

export type RefreshWebSessionResult =
  | { kind: 'success'; session: AuthSessionResponse }
  | { kind: 'terminal' }
  | { kind: 'unavailable' };

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

export const refreshWebSession = async (): Promise<RefreshWebSessionResult> => {
  try {
    const response = await apiFetch('/api/v1/auth/refresh', { method: 'POST' });
    if (response.status === 401) {
      return { kind: 'terminal' };
    }
    if (!response.ok) {
      return { kind: 'unavailable' };
    }
    return {
      kind: 'success',
      session: await response.json() as AuthSessionResponse,
    };
  } catch {
    return { kind: 'unavailable' };
  }
};

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
