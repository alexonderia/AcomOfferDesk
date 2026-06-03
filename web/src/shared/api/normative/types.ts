export type NormativeFileStatus = 'actual' | 'outdated';

export type NormativeFileItem = {
  id: number;
  file_id: number;
  original_name: string;
  status: NormativeFileStatus;
  created_at: string;
  download_url: string;
};

export const normativeFileStatusLabels: Record<NormativeFileStatus, string> = {
  actual: 'Актуальный',
  outdated: 'Неактуальный',
};
