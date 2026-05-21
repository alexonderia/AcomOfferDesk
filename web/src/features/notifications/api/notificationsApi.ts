import { fetchJson } from '@shared/api/client';
import type { Notification, NotificationQueryParams, UnreadCount } from '../model/types';

type NotificationsListResponse = {
  data: {
    items: Notification[];
    limit: number;
    offset: number;
  };
};

type NotificationsUnreadCountResponse = {
  data: UnreadCount;
};

type MarkNotificationReadResponse = {
  data: {
    notification_id: number;
    read_at: string;
  };
};

type MarkAllNotificationsReadResponse = {
  data: {
    updated_count: number;
  };
};

export const getNotifications = async (
  params: NotificationQueryParams = {}
): Promise<NotificationsListResponse['data']> => {
  const limit = params.limit ?? 50;
  const offset = params.offset ?? 0;
  const query = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });

  const response = await fetchJson<NotificationsListResponse>(
    `/api/v1/notifications?${query.toString()}`,
    { method: 'GET' },
    'Не удалось загрузить уведомления'
  );

  return response.data;
};

export const getUnreadCount = async (): Promise<UnreadCount> => {
  const response = await fetchJson<NotificationsUnreadCountResponse>(
    '/api/v1/notifications/unread-count',
    { method: 'GET' },
    'Не удалось загрузить количество непрочитанных уведомлений'
  );

  return response.data;
};

export const markNotificationRead = async (
  notificationId: number
): Promise<MarkNotificationReadResponse['data']> => {
  const response = await fetchJson<MarkNotificationReadResponse>(
    `/api/v1/notifications/${notificationId}/read`,
    { method: 'PATCH' },
    'Не удалось отметить уведомление как прочитанное'
  );

  return response.data;
};

export const markAllNotificationsRead = async (): Promise<MarkAllNotificationsReadResponse['data']> => {
  const response = await fetchJson<MarkAllNotificationsReadResponse>(
    '/api/v1/notifications/read-all',
    { method: 'PATCH' },
    'Не удалось отметить уведомления как прочитанные'
  );

  return response.data;
};

