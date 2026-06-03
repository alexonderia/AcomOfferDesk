import { fetchJson } from '../client';

export type InviteContractorsRequest = {
  emails: string[];
  normativeFileId: number;
};

export type InviteContractorsFailure = {
  email: string;
  reason: string;
};

export type InviteContractorsResponse = {
  data: {
    sent: string[];
    failed: InviteContractorsFailure[];
    invalid: string[];
  };
};

export const inviteContractors = async (
  payload: InviteContractorsRequest
): Promise<InviteContractorsResponse> => {
  return fetchJson<InviteContractorsResponse>(
    '/api/v1/contractors/invite',
    {
      method: 'POST',
      body: JSON.stringify({
        emails: payload.emails,
        normative_file_id: payload.normativeFileId,
      }),
    },
    'Ошибка отправки приглашений контрагентам'
  );
};
