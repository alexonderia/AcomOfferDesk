import { fetchJson } from '../client';

export type RequestEconomist = {
  user_id: string;
  full_name: string | null;
  role: string;
  unavailable_period: {
    id: number;
    status: string;
    started_at: string;
    ended_at: string;
  } | null;
};

type ResponsePayload = {
  data: {
    items: RequestEconomist[];
  };
};

export const getRequestEconomists = async (requestId: string): Promise<RequestEconomist[]> => {
  const response = await fetchJson<ResponsePayload>(
    `/api/v1/requests/${encodeURIComponent(requestId)}/eligible-owners`,
    { method: 'GET' },
    'Ошибка загрузки списка ответственных'
  );

  return response.data.items ?? [];
};
