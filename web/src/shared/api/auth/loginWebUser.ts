import { fetchEmpty, fetchJson } from '../client';

export type AuthSessionResponse = {
  data: {
    access_token: string;
    token_type: string;
    access_token_expires_at: number;
    user_id: string;
    login: string;
    role_id: number;
    status: string;
    auth_provider?: string;
    business_access?: boolean;
    onboarding_state?: string | null;
    permissions?: string[];
    app_roles?: string[];
    delegation_roles?: string[];
  };
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
