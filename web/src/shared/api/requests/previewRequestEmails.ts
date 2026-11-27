import { fetchJson } from '../client';

export type RequestEmailPreviewAttachment = {
  name: string;
  size_bytes: number;
  download_url: string | null;
  upload_index: number | null;
};

export type RequestEmailPreview = {
  messages: Array<{
    to_email: string;
    kind: string;
    subject: string;
    html_content: string;
    text_content: string;
    attachments: RequestEmailPreviewAttachment[];
  }>;
  warnings: string[];
};

export type DraftRequestEmailPreviewPayload = {
  request_id: string;
  description: string | null;
  deadline_at: string;
  normative_file_id: number;
  files: Array<{ name: string; size_bytes: number }>;
  additional_emails: string[];
  hidden_contractor_ids: string[];
};

export const previewRequestEmails = async (
  payload: DraftRequestEmailPreviewPayload | { requestId: string; additional_emails: string[] },
  signal: AbortSignal,
): Promise<RequestEmailPreview> => {
  const { data } = await fetchJson<{ data: RequestEmailPreview }>(
    'requestId' in payload
      ? `/api/v1/requests/${encodeURIComponent(payload.requestId)}/email-notifications/preview`
      : '/api/v1/requests/email-preview',
    { method: 'POST', body: JSON.stringify(payload), signal },
    'Не удалось подготовить проверку писем',
  );
  return data;
};
