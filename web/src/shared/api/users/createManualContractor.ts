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
    outcome?: 'created' | 'duplicate_found';
    duplicate?: {
      company_name: string;
      inn: string;
      company_mail?: string | null;
    } | null;
  };
};

export type CreateManualContractorResult = {
  userId: string;
  outcome: 'created' | 'duplicate_found';
  duplicate: {
    companyName: string;
    inn: string;
    companyMail: string | null;
  } | null;
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
    userId: response.data.user_id,
    outcome: response.data.outcome ?? 'created',
    duplicate: response.data.duplicate
      ? {
          companyName: response.data.duplicate.company_name,
          inn: response.data.duplicate.inn,
          companyMail: response.data.duplicate.company_mail ?? null,
        }
      : null,
  };
};
