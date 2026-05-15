import type { Location } from 'react-router-dom';
import type { Notification } from './types';

const OFFER_WORKSPACE_PATH_PATTERN = /^\/offers\/(\d+)\/workspace(?:\/|$)/i;

const toPositiveNumber = (value: unknown): number | null => {
  if (typeof value === 'number' && Number.isInteger(value) && value > 0) {
    return value;
  }
  if (typeof value !== 'string') {
    return null;
  }
  const parsed = Number(value.trim());
  if (!Number.isInteger(parsed) || parsed <= 0) {
    return null;
  }
  return parsed;
};

const resolveWorkspaceOfferIdFromPath = (pathname: string): number | null => {
  const match = pathname.match(OFFER_WORKSPACE_PATH_PATTERN);
  if (!match) {
    return null;
  }
  return toPositiveNumber(match[1]);
};

const resolveOfferIdFromNotification = (notification: Notification): number | null => {
  const payload = notification.payload ?? {};
  const payloadOfferId =
    toPositiveNumber(payload.offer_id) ??
    toPositiveNumber(payload.chat_id);
  if (payloadOfferId) {
    return payloadOfferId;
  }

  if (notification.link_url) {
    try {
      const parsed = notification.link_url.startsWith('/')
        ? new URL(notification.link_url, window.location.origin)
        : new URL(notification.link_url);
      return resolveWorkspaceOfferIdFromPath(parsed.pathname);
    } catch {
      return null;
    }
  }

  return null;
};

export const isNotificationForCurrentOpenChat = (
  notification: Notification,
  location: Pick<Location, 'pathname'>
): boolean => {
  if (notification.type !== 'message.created') {
    return false;
  }

  const currentOfferId = resolveWorkspaceOfferIdFromPath(location.pathname);
  if (!currentOfferId) {
    return false;
  }

  const notificationOfferId = resolveOfferIdFromNotification(notification);
  if (!notificationOfferId) {
    return false;
  }

  return notificationOfferId === currentOfferId;
};
