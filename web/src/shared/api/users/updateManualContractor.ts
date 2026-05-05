import { fetchJson } from '../client';

export type UpdateManualContractorPayload = {
  login?: string;
  password?: string;
  full_name?: string;
  phone?: string;
  mail?: string;
  company_name?: string;
  inn?: string;
  company_phone?: string;
  company_mail?: string;
  address?: string;
  note?: string;
};

type ApiResponse = {
  data: {
    user_id: string;
  };
};

export type UpdateManualContractorResult = {
  userId: string;
};

export const updateManualContractor = async (
  userId: string,
  payload: UpdateManualContractorPayload
): Promise<UpdateManualContractorResult> => {
  const response = await fetchJson<ApiResponse>(
    `/api/v1/users/${encodeURIComponent(userId)}/manual-contractor`,
    {
      method: 'PATCH',
      body: JSON.stringify(payload)
    },
    'Не удалось обновить данные контрагента'
  );

  return {
    userId: response.data.user_id
  };
};

