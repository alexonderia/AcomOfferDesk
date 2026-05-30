import { fetchJson } from '../client';

export type RequestIdAvailabilityResponse = {
  available: boolean;
  detail?: string | null;
  reason?: string | null;
};

export const checkRequestIdAvailability = async (requestId: string): Promise<RequestIdAvailabilityResponse> => {
  const query = new URLSearchParams({ id: requestId.trim() });
  return fetchJson<RequestIdAvailabilityResponse>(
    `/api/v1/requests/check-id?${query.toString()}`,
    { method: 'GET' },
    'Не удалось проверить номер заявки'
  );
};
