import { fetchJson } from '../client';

export type RequestContractorItem = {
  user_id: string;
  full_name: string | null;
  company_name: string | null;
  mail: string | null;
  company_mail: string | null;
};

type RequestContractorListResponse = {
  data: {
    items: RequestContractorItem[];
  };
};

export type GetRequestContractorsResult = {
  items: RequestContractorItem[];
};

export const getRequestContractors = async (requestId?: string): Promise<GetRequestContractorsResult> => {
  const response = await fetchJson<RequestContractorListResponse>(
    requestId
      ? `/api/v1/requests/${encodeURIComponent(requestId)}/offers/manual/eligible-contractors`
      : '/api/v1/users/request-contractors',
    { method: 'GET' },
    'Ошибка загрузки контрагентов'
  );

  return {
    items: response.data.items.map((item) => ({
      user_id: item.user_id,
      full_name: item.full_name ?? null,
      company_name: item.company_name ?? null,
      mail: item.mail ?? null,
      company_mail: item.company_mail ?? null
    }))
  };
};
