import { fetchJson } from '../client';

export type ManualContractorDuplicate = {
  userId: string;
  fullName: string | null;
  phone: string | null;
  mail: string | null;
  companyName: string | null;
  inn: string | null;
  companyPhone: string | null;
  companyMail: string | null;
  address: string | null;
  note: string | null;
  status: string;
  createdAt: string | null;
  updatedAt: string | null;
};

type DuplicatePayload = {
  user_id: string;
  full_name?: string | null;
  phone?: string | null;
  mail?: string | null;
  company_name?: string | null;
  inn?: string | null;
  company_phone?: string | null;
  company_mail?: string | null;
  address?: string | null;
  note?: string | null;
  status: string;
  created_at?: string | null;
  updated_at?: string | null;
};

type DuplicateResponse = { data: { items: DuplicatePayload[] } };

export const getManualContractorDuplicates = async (query: {
  companyName?: string;
  inn?: string;
  companyMail?: string;
}): Promise<ManualContractorDuplicate[]> => {
  const params = new URLSearchParams();
  if (query.companyName?.trim()) params.set('company_name', query.companyName.trim());
  if (query.inn?.trim()) params.set('inn', query.inn.trim());
  if (query.companyMail?.trim()) params.set('company_mail', query.companyMail.trim());
  const suffix = params.toString();
  const response = await fetchJson<DuplicateResponse>(
    `/api/v1/users/manual-contractor-duplicates${suffix ? `?${suffix}` : ''}`,
    {},
    'Не удалось проверить похожих контрагентов'
  );
  return response.data.items.map((item) => ({
    userId: item.user_id,
    fullName: item.full_name ?? null,
    phone: item.phone ?? null,
    mail: item.mail ?? null,
    companyName: item.company_name ?? null,
    inn: item.inn ?? null,
    companyPhone: item.company_phone ?? null,
    companyMail: item.company_mail ?? null,
    address: item.address ?? null,
    note: item.note ?? null,
    status: item.status,
    createdAt: item.created_at ?? null,
    updatedAt: item.updated_at ?? null,
  }));
};
