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
    permissions?: string[];
  };
};

export type GetRequestContractorsResult = {
  items: RequestContractorItem[];
  permissions: string[];
};

export const getRequestContractors = async (): Promise<GetRequestContractorsResult> => {
  const response = await fetchJson<RequestContractorListResponse>(
    '/api/v1/users/request-contractors',
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
    })),
    permissions: response.data.permissions ?? []
  };
};
