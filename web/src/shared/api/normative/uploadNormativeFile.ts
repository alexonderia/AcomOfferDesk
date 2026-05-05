import { fetchJson } from '@shared/api/client';

type UploadNormativeFileResponse = {
  data: {
    normative_id: number;
    file_id: number;
  };
};

export const uploadNormativeFile = async (file: File, normativeId = 1): Promise<number> => {
  const formData = new FormData();
  formData.append('file', file, file.name);

  const response = await fetchJson<UploadNormativeFileResponse>(
    `/api/v1/normative-files/${normativeId}`,
    {
      method: 'POST',
      body: formData
    },
    'Не удалось загрузить нормативный документ'
  );

  return response.data.file_id;
};
