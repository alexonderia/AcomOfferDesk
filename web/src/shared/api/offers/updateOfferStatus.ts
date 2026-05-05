import { fetchJson } from '../client';

export type UpdateOfferStatusPayload = {
  offer_id: number;
  status: string;
};

type UpdateOfferStatusApiResponse = {
  data?: {
    offer_id?: number;
    status?: string;
  };
  offer?: {
    id?: number;
    status?: string;
  };
};

export type UpdateOfferStatusResponse = {
  offer: {
    id: number;
    status: string;
  };
};

export const updateOfferStatus = async (
  payload: UpdateOfferStatusPayload
): Promise<UpdateOfferStatusResponse> => {
  const response = await fetchJson<UpdateOfferStatusApiResponse>(
    `/api/v1/offers/${payload.offer_id}/status`,
    {
      method: 'PATCH',
      body: JSON.stringify({ status: payload.status })
    },
    'Ошибка обновления статуса КП'
  );
  return {
    offer: {
      id: response.data?.offer_id ?? response.offer?.id ?? payload.offer_id,
      status: response.data?.status ?? response.offer?.status ?? payload.status
    }
  };
};
