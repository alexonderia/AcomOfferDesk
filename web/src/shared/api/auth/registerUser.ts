import { fetchJson } from '../client';

export type RegisterUserPayload = {
  login: string;
  password?: string;
  role_id: number;
  id_parent?: string;
  full_name?: string;
  phone?: string;
  mail?: string;
  unit_id?: number;
};

export type RegisterUserResponse = {
  data: {
    user_id: string;
    role_id: number;
    status: string;
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
