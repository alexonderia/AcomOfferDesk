import { fetchJson } from '../client';

export type OfferContractorInfo = {
  user_id: string;
  full_name: string | null;
  phone: string | null;
  mail: string | null;
  company_name: string | null;
  inn: string | null;
  company_phone: string | null;
  company_mail: string | null;
  address: string | null;
  note: string | null;
};

type ApiResponse = {
  data: OfferContractorInfo;
};

export const getOfferContractorInfo = async (contractorUserId: string): Promise<OfferContractorInfo> => {
  const queryParams = new URLSearchParams({ id_user: contractorUserId });
  const response = await fetchJson<ApiResponse>(
    `/api/v1/offers?${queryParams.toString()}`,
    { method: 'GET' },
    'Ошибка загрузки информации о контрагенте'
  );

  return response.data;
};
