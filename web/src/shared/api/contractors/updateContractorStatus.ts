import { fetchJson } from '../client';

type UpdateContractorStatusPayload = {
  user_status: 'review' | 'active' | 'inactive' | 'blacklist';
};

type UpdateContractorStatusResponse = {
  data: {
    user_id: string;
    user_status: string;
  };
};

export const updateContractorStatus = async (
  contractorId: string,
  payload: UpdateContractorStatusPayload
): Promise<UpdateContractorStatusResponse> =>
  fetchJson<UpdateContractorStatusResponse>(
    `/api/v1/contractors/${encodeURIComponent(contractorId)}/status`,
    {
      method: 'PATCH',
      body: JSON.stringify(payload),
    },
    'Не удалось обновить статус контрагента'
  );
