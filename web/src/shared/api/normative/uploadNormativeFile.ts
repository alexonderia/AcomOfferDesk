import { fetchJson } from '@shared/api/client';

type UploadNormativeFileResponse = {
  data: {
    normative_id: number;
    file_id: number;
  };
};

export const uploadNormativeFile = async (file: File): Promise<number> => {
  return await uploadNormativeFileToEndpoint('/api/v1/normative-files', file);
};

export const replaceNormativeFile = async (normativeId: number, file: File): Promise<number> => {
  return await uploadNormativeFileToEndpoint(`/api/v1/normative-files/${normativeId}`, file);
};

const uploadNormativeFileToEndpoint = async (url: string, file: File): Promise<number> => {
  const formData = new FormData();
  formData.append('file', file, file.name);

  const response = await fetchJson<UploadNormativeFileResponse>(
    url,
    {
      method: 'POST',
      body: formData
    },
    'Не удалось загрузить нормативный документ'
  );

  return response.data.file_id;
};
