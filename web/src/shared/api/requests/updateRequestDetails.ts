import { fetchEmpty, fetchJson } from '../client';

export type RequestStatus = 'open' | 'review' | 'closed' | 'cancelled';

export type UpdateRequestDetailsPayload = {
  requestId: number;
  status?: RequestStatus;
  deadline_at?: string | null;
  owner_user_id?: string;
  initial_amount?: number;
  final_amount?: number;
  id_plan?: number | null;
};

type UpdateRequestResponse = {
  data?: {
    item?: {
      request_id?: number;
      status?: string;
      deadline_at?: string | null;
      owner_user_id?: string;
    };
  };
};

export const updateRequestDetails = async (
  payload: UpdateRequestDetailsPayload
): Promise<UpdateRequestResponse> => {
  const body: Record<string, string | number | null> = {};

  if (payload.status !== undefined) {
    body.status = payload.status;
  }

  if (payload.deadline_at !== undefined) {
    body.deadline_at = payload.deadline_at;
  }

  if (payload.owner_user_id !== undefined) {
    body.owner_user_id = payload.owner_user_id;
  }

  if (payload.initial_amount !== undefined) {
    body.initial_amount = payload.initial_amount;
  }

  if (payload.final_amount !== undefined) {
    body.final_amount = payload.final_amount;
  }

  if (payload.id_plan !== undefined) {
    body.id_plan = payload.id_plan;
  }

  return fetchJson<UpdateRequestResponse>(
    `/api/v1/requests/${payload.requestId}`,
    {
      method: 'PATCH',
      body: JSON.stringify(body)
    },
    'Ошибка сохранения заявки'
  );
};

export const deleteRequestFile = async (requestId: number, fileId: number) => {
  await fetchEmpty(
    `/api/v1/requests/${requestId}/files/${fileId}`,
    {
      method: 'DELETE'
    },
    'Ошибка удаления файла'
  );
};

export const uploadRequestFile = async (requestId: number, file: File) => {
  const formData = new FormData();
  formData.append('file', file, file.name);

  await fetchJson(
    `/api/v1/requests/${requestId}/files`,
    {
      method: 'POST',
      body: formData
    },
    'Ошибка прикрепления файла'
  );

};
