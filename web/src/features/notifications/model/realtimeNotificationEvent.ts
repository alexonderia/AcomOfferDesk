import type { RealtimeEnvelope } from '@shared/ws/realtimeSocket';
import type { Notification, NotificationSeverity } from './types';

type NotificationCreatedEventPayload = {
  notification: Notification;
  hasUnread: boolean;
};

const isObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null;

const toOptionalInt = (value: unknown): number | null => {
  if (typeof value === 'number' && Number.isInteger(value)) {
    return value;
  }
  if (typeof value !== 'string') {
    return null;
  }
  const parsed = Number(value.trim());
  if (!Number.isInteger(parsed)) {
    return null;
  }
  return parsed;
};

const toSeverity = (value: unknown): NotificationSeverity => {
  if (value === 'success' || value === 'warning' || value === 'error') {
    return value;
  }
  return 'info';
};

const toOptionalString = (value: unknown): string | null => {
  if (typeof value !== 'string') {
    return null;
  }
  const normalized = value.trim();
  return normalized.length > 0 ? normalized : null;
};

const toPayloadObject = (value: unknown): Record<string, unknown> =>
  isObject(value) ? value : {};

export const parseNotificationCreatedEvent = (
  event: RealtimeEnvelope
): NotificationCreatedEventPayload | null => {
  if (event.type !== 'notification.created' || !isObject(event.data)) {
    return null;
  }

  const data = event.data;
  const notificationRaw = data.notification;
  if (!isObject(notificationRaw)) {
    return null;
  }

  const id = toOptionalInt(notificationRaw.id);
  const type = toOptionalString(notificationRaw.type);
  const title = toOptionalString(notificationRaw.title);
  const body = toOptionalString(notificationRaw.body);
  const createdAt = toOptionalString(notificationRaw.created_at);

  if (id === null || type === null || title === null || body === null || createdAt === null) {
    return null;
  }

  const notification: Notification = {
    id,
    type,
    severity: toSeverity(notificationRaw.severity),
    title,
    body,
    entity_type: toOptionalString(notificationRaw.entity_type),
    entity_id: toOptionalInt(notificationRaw.entity_id),
    link_url: toOptionalString(notificationRaw.link_url),
    payload: toPayloadObject(notificationRaw.payload),
    read_at: toOptionalString(notificationRaw.read_at),
    created_at: createdAt,
  };

  return {
    notification,
    hasUnread: data.has_unread !== false,
  };
};
