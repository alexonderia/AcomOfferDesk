import type { Notification } from './types';

const TRACKING_ONLY_FLAG = 'true';
const SYSTEM_TOAST_CHANNEL = 'system';

const isTrackingOnlyValue = (value: unknown): boolean => {
  if (value === true) {
    return true;
  }
  if (typeof value !== 'string') {
    return false;
  }
  return value.trim().toLowerCase() === TRACKING_ONLY_FLAG;
};

export const isVisibleNotification = (
  notification: Pick<Notification, 'payload'>
): boolean => !isTrackingOnlyValue(notification.payload?.tracking_only);

export const resolveNotificationToastChannel = (
  notification: Pick<Notification, 'payload'>
): string | null => {
  const rawChannel = notification.payload?.toast_channel;
  if (typeof rawChannel !== 'string') {
    return null;
  }
  const normalizedChannel = rawChannel.trim().toLowerCase();
  return normalizedChannel || null;
};

export const isSystemToastNotification = (
  notification: Pick<Notification, 'payload'>
): boolean => resolveNotificationToastChannel(notification) === SYSTEM_TOAST_CHANNEL;
