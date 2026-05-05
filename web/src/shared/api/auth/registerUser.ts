import { fetchJson } from '../client';
import type { AuthLink } from './loginWebUser';

export type RegisterUserPayload = {
  login: string;
  password?: string;
  role_id: number;
  id_parent?: string;
  full_name?: string;
  phone?: string;
  mail?: string;
};

export type RegisterUserResponse = {
  data: {
    user_id: string;
    role_id: number;
    status: string;
  };
  _links: {
    self: AuthLink;
  };
};

export const registerUser = async (payload: RegisterUserPayload): Promise<RegisterUserResponse> =>
  fetchJson<RegisterUserResponse>(
    '/api/v1/users/register',
    {
      method: 'POST',
      body: JSON.stringify(payload)
    },
    'Ошибка создания пользователя'
  );
