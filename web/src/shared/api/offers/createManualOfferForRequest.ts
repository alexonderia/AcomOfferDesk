import { fetchJson } from '../client';

export type ManualOfferExistingContractorPayload = {
  contractor_mode: 'existing';
  contractor_user_id: string;
  offer_amount?: number | null;
  files?: File[];
};

export type ManualOfferNewContractorPayload = {
  contractor_mode: 'new';
  company_name: string;
  inn: string;
  company_phone: string;
  company_mail?: string;
  address?: string;
  note?: string;
  offer_amount?: number | null;
  files?: File[];
};

export type ManualOfferCreatePayload =
  | ManualOfferExistingContractorPayload
  | ManualOfferNewContractorPayload;

type ApiResponse = {
  data: {
    offer_id: number;
    request_id: number;
    contractor_user_id: string;
    contractor_created: boolean;
  };
};

export type ManualOfferCreateResult = {
  offerId: number;
  requestId: number;
  contractorUserId: string;
  contractorCreated: boolean;
  workspacePath: string;
};

export const createManualOfferForRequest = async (
  requestId: number,
  payload: ManualOfferCreatePayload
): Promise<ManualOfferCreateResult> => {
  const body = new FormData();
  body.append('contractor_mode', payload.contractor_mode);

  if (payload.contractor_mode === 'existing') {
    body.append('contractor_user_id', payload.contractor_user_id);
  } else {
    body.append('company_name', payload.company_name);
    body.append('inn', payload.inn);
    body.append('company_phone', payload.company_phone);
    if (payload.company_mail?.trim()) {
      body.append('company_mail', payload.company_mail.trim());
    }
    if (payload.address?.trim()) {
      body.append('address', payload.address.trim());
    }
    if (payload.note?.trim()) {
      body.append('note', payload.note.trim());
    }
  }

  if (typeof payload.offer_amount === 'number' && Number.isFinite(payload.offer_amount)) {
    body.append('offer_amount', String(payload.offer_amount));
  }

  for (const file of payload.files ?? []) {
    body.append('files', file);
  }

  const response = await fetchJson<ApiResponse>(
    `/api/v1/requests/${requestId}/offers/manual`,
    {
      method: 'POST',
      body
    },
    'Не удалось создать КП вручную'
  );

  return {
    offerId: response.data.offer_id,
    requestId: response.data.request_id,
    contractorUserId: response.data.contractor_user_id,
    contractorCreated: response.data.contractor_created,
    workspacePath: `/offers/${response.data.offer_id}/workspace`
  };
};
