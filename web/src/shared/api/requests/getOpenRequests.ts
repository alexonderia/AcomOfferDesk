import { fetchJson } from '../client';
import type { GetRequestsResponse } from './getRequests';
import type { FileEntity } from '@entities/request';
import { normalizeRequestActions } from '../mappers';

type ApiResponse = {
  data: {
    items: Array<{
      request_id: number;
      description: string | null;
      status: string;
      status_label: string;
      deadline_at: string;
      created_at: string;
      updated_at: string;
      closed_at: string | null;
      owner_user_id: string;
      owner_full_name?: string | null;
      chosen_offer_id: number | null;
      files: FileEntity[];
      actions?: {
        can_view_details?: boolean;
        can_view_amounts?: boolean;
        can_open_contractor_view?: boolean;
        can_edit?: boolean;
        can_change_owner?: boolean;
        can_upload_files?: boolean;
        can_delete_files?: boolean;
        can_send_email_notifications?: boolean;
        can_mark_deleted_alert_viewed?: boolean;
        can_create_offer?: boolean;
      };
    }>;
  };
};

export const getOpenRequests = async (): Promise<GetRequestsResponse> => {
  const response = await fetchJson<ApiResponse>(
    '/api/v1/requests/open',
    { method: 'GET' },
    'Ошибка загрузки открытых заявок'
  );

  return {
    requests: response.data.items.map((item) => ({
      id: item.request_id,
      id_user: item.owner_user_id,
      owner_full_name: item.owner_full_name ?? null,
      status: item.status,
      status_label: item.status_label,
      deadline_at: item.deadline_at,
      closed_at: item.closed_at,
      id_offer: item.chosen_offer_id,
      description: item.description,
      created_at: item.created_at,
      updated_at: item.updated_at,
      count_submitted: 0,
      count_deleted_alert: 0,
      count_accepted_total: 0,
      count_rejected_total: 0,
      files: item.files,
      actions: normalizeRequestActions(item.actions)
    }))
  };
};
