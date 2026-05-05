import { fetchJson } from '../client';

export type MarkDeletedAlertViewedPayload = {
  request_id: number;
};

export type MarkDeletedAlertViewedResponse = {
  status: 'ok';
  request_offer_stats: {
    request_id: number;
    count_deleted_alert: number;
    updated_at: string;
  };
};

type ApiResponse = {
  status?: 'ok';
  request_offer_stats?: {
    request_id?: number;
    count_deleted_alert?: number;
    updated_at?: string;
  };
  data?: {
    request_offer_stats?: {
      request_id?: number;
      count_deleted_alert?: number;
      updated_at?: string;
    };
    request_id?: number;
    count_deleted_alert?: number;
    updated_at?: string;
  };
};

export const markDeletedAlertViewed = async (
  payload: MarkDeletedAlertViewedPayload
): Promise<MarkDeletedAlertViewedResponse> => {
  const response = await fetchJson<ApiResponse>(
    '/api/v1/requests/deleted-alerts/viewed',
    {
      method: 'PATCH',
      body: JSON.stringify(payload)
    },
    'Не удалось отметить уведомление об отмене сделки'
  );
  const stats =
    response.request_offer_stats ??
    response.data?.request_offer_stats ?? {
      request_id: response.data?.request_id,
      count_deleted_alert: response.data?.count_deleted_alert,
      updated_at: response.data?.updated_at
    };

  return {
    status: response.status ?? 'ok',
    request_offer_stats: {
      request_id: stats.request_id ?? payload.request_id,
      count_deleted_alert: stats.count_deleted_alert ?? 0,
      updated_at: stats.updated_at ?? new Date().toISOString()
    }
  };
};