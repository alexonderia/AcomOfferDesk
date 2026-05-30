import { fetchJson } from '../client';

type SendRequestEmailNotificationsPayload = {
  requestId: string;
  additional_emails: string[];
};

type SendRequestEmailNotificationsResponse = {
  data: {
    request_id: string;
    sent_to: string[];
  };
};

export const sendRequestEmailNotifications = async (
  payload: SendRequestEmailNotificationsPayload
): Promise<SendRequestEmailNotificationsResponse> => {
  return fetchJson<SendRequestEmailNotificationsResponse>(
    `/api/v1/requests/${payload.requestId}/email-notifications`,
    {
      method: 'POST',
      body: JSON.stringify({
        additional_emails: payload.additional_emails
      })
    },
    'Ошибка отправки писем'
  );
};
