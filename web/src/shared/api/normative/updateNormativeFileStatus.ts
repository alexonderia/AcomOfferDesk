import { fetchJson } from '../client';
import type { NormativeFileItem, NormativeFileStatus } from './types';

type NormativeFileStatusUpdateResponse = {
  data: NormativeFileItem;
};

export const updateNormativeFileStatus = async (
  normativeId: number,
  status: NormativeFileStatus
): Promise<NormativeFileItem> => {
  const response = await fetchJson<NormativeFileStatusUpdateResponse>(
    `/api/v1/normative-files/${normativeId}/status`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    },
    'Не удалось обновить статус нормативного документа'
  );

  return response.data;
};
