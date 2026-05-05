import { fetchJson  } from '../client';

export type CreateRequestPayload = {
  description?: string | null;
  deadline_at: string;
  initial_amount?: string | number | null;
  files: File[];
  additional_emails?: string[];
  hidden_contractor_ids?: string[];
};

export type CreateRequestResponse = {
  data: {
    request_id: number;
    file_ids: number[];
  };
};

export const createRequest = async (payload: CreateRequestPayload): Promise<CreateRequestResponse> => {
  const formData = new FormData();
  formData.append('deadline_at', payload.deadline_at);

  
  if (payload.description) {
    formData.append('description', payload.description);
  }

  if (payload.initial_amount !== undefined && payload.initial_amount !== null && String(payload.initial_amount).trim() !== '') {
    formData.append('initial_amount', String(payload.initial_amount));
  }

  payload.files.forEach((file) => {
    formData.append('files', file, file.name);
  });

  payload.additional_emails?.forEach((email) => {
    formData.append('additional_emails', email);
  });

  payload.hidden_contractor_ids?.forEach((contractorId) => {
    formData.append('hidden_contractor_ids', contractorId);
  });

  return fetchJson<CreateRequestResponse>(
    '/api/v1/requests',
    {
      method: 'POST',
      body: formData
    },
    'Ошибка создания заявки'
  );
};
