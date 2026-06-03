import { fetchJson } from '../client';
import type { NormativeFileItem, NormativeFileStatus } from './types';

type NormativeFileListResponse = {
  data: {
    items: NormativeFileItem[];
  };
};

export const getNormativeFiles = async (status?: NormativeFileStatus): Promise<NormativeFileItem[]> => {
  const query = status ? `?status=${encodeURIComponent(status)}` : '';
  const response = await fetchJson<NormativeFileListResponse>(
    `/api/v1/normative-files${query}`,
    { method: 'GET' },
    'Не удалось загрузить нормативные документы'
  );

  return response.data.items;
};
