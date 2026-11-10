import { fetchJson } from '../client';

export type EmployeeProfile = {
  user_id: string;
  role_id: number;
  status: string;
  full_name: string | null;
  phone: string | null;
  mail: string | null;
};

export const getEmployeeProfile = async (userId: string, signal?: AbortSignal): Promise<EmployeeProfile> => {
  const response = await fetchJson<{ data: EmployeeProfile }>(
    `/api/v1/users/${encodeURIComponent(userId)}/details`,
    { method: 'GET', signal, cache: 'no-store' },
    'Не удалось загрузить профиль сотрудника',
  );
  return response.data;
};
