import { fetchJson } from '../client';

type ApiResponse = {
  data: {
    offer_id: number;
    request_id: string;
  };
};

export type CreatedOffer = {
  offerId: number;
  requestId: string;
  workspacePath: string;
};

export const createOfferForRequest = async (
  requestId: string,
  payload?: { offer_amount?: number }
): Promise<CreatedOffer> => {
  const response = await fetchJson<ApiResponse>(
    `/api/v1/requests/${requestId}/offers`,
    {
      method: 'POST',
      body: JSON.stringify(payload ?? {})
    },
    'Не удалось создать отклик'
  );

  return {
    offerId: response.data.offer_id,
    requestId: response.data.request_id,
    workspacePath: `/offers/${response.data.offer_id}/workspace`
  };
};
