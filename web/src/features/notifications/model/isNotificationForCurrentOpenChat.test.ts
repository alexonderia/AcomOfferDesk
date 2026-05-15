import { describe, expect, it } from 'vitest';
import type { Notification } from './types';
import { isNotificationForCurrentOpenChat } from './isNotificationForCurrentOpenChat';

const buildNotification = (offerId: number): Notification => ({
  id: 1,
  type: 'message.created',
  severity: 'info',
  title: 'New message',
  body: 'Body',
  entity_type: 'message',
  entity_id: 1,
  link_url: `/offers/${offerId}/workspace`,
  payload: { offer_id: offerId, chat_id: offerId, message_id: 1 },
  read_at: null,
  created_at: '2026-05-14T10:00:00Z',
});

describe('isNotificationForCurrentOpenChat', () => {
  it('returns true for matching offer workspace route', () => {
    const notification = buildNotification(11);
    const result = isNotificationForCurrentOpenChat(notification, { pathname: '/offers/11/workspace' });
    expect(result).toBe(true);
  });

  it('returns false for different workspace route', () => {
    const notification = buildNotification(11);
    const result = isNotificationForCurrentOpenChat(notification, { pathname: '/offers/15/workspace' });
    expect(result).toBe(false);
  });
});
