import { fetchJson } from '../client';

export type CreateManualContractorPayload = {
  company_name: string;
  inn: string;
  company_phone: string;
  company_mail?: string;
  address?: string;
  note?: string;
};

type ApiResponse = {
  data: {
    user_id: string;
  };
};

export type CreateManualContractorResult = {
  userId: string;
};

export const createManualContractor = async (
  payload: CreateManualContractorPayload
): Promise<CreateManualContractorResult> => {
  const response = await fetchJson<ApiResponse>(
    '/api/v1/users/manual-contractor',
    {
      method: 'POST',
      body: JSON.stringify(payload)
    },
    'Не удалось создать контрагента'
  );

  return {
    userId: response.data.user_id
  };
};
