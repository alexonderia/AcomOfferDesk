import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useNotifications } from './useNotifications';

const getNotificationsMock = vi.fn();
const getUnreadCountMock = vi.fn();
const markNotificationReadMock = vi.fn();
const markAllNotificationsReadMock = vi.fn();

vi.mock('../api/notificationsApi', () => ({
  getNotifications: (...args: unknown[]) => getNotificationsMock(...args),
  getUnreadCount: (...args: unknown[]) => getUnreadCountMock(...args),
  markNotificationRead: (...args: unknown[]) => markNotificationReadMock(...args),
  markAllNotificationsRead: (...args: unknown[]) => markAllNotificationsReadMock(...args),
}));

describe('useNotifications', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    getNotificationsMock.mockReset();
    getUnreadCountMock.mockReset();
    markNotificationReadMock.mockReset();
    markAllNotificationsReadMock.mockReset();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('polls unread boolean by interval when enabled', async () => {
    getUnreadCountMock.mockResolvedValue({ count: 5 });

    const { result } = renderHook(() =>
      useNotifications({ enabled: true, pollingIntervalMs: 1_000 })
    );

    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(result.current.hasUnread).toBe(true);

    await act(async () => {
      vi.advanceTimersByTime(2_100);
      await Promise.resolve();
    });

    expect(getUnreadCountMock).toHaveBeenCalledTimes(3);
  });

  it('applies realtime notification and enables unread dot state', async () => {
    getUnreadCountMock.mockResolvedValue({ count: 0 });

    const { result } = renderHook(() => useNotifications({ enabled: true, pollingIntervalMs: 10_000 }));

    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });

    await act(async () => {
      result.current.applyRealtimeNotificationCreated({
        id: 101,
        type: 'message.created',
        severity: 'info',
        title: 'Realtime message',
        body: 'Body',
        entity_type: 'message',
        entity_id: 101,
        link_url: '/offers/10/workspace',
        payload: { offer_id: 10 },
        read_at: null,
        created_at: '2026-05-18T10:00:00Z',
      });
    });

    expect(result.current.hasUnread).toBe(true);
    expect(result.current.items[0]?.id).toBe(101);
  });

  it('ignores tracking-only realtime notification rows', async () => {
    getUnreadCountMock.mockResolvedValue({ count: 0 });

    const { result } = renderHook(() => useNotifications({ enabled: true, pollingIntervalMs: 10_000 }));

    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });

    await act(async () => {
      result.current.applyRealtimeNotificationCreated({
        id: 303,
        type: 'system.warning',
        severity: 'info',
        title: 'Tracking email operation',
        body: 'Tracking email operation',
        entity_type: 'request',
        entity_id: 77,
        link_url: '/requests/77',
        payload: { tracking_only: 'true', operation_id: 'op-1' },
        read_at: null,
        created_at: '2026-05-18T10:00:00Z',
      });
    });

    expect(result.current.hasUnread).toBe(false);
    expect(result.current.items).toEqual([]);
  });

  it('markAllAsRead clears unread dot state', async () => {
    getUnreadCountMock.mockResolvedValue({ count: 0 });
    markAllNotificationsReadMock.mockResolvedValue({ updated_count: 1 });

    const { result } = renderHook(() => useNotifications({ enabled: true, pollingIntervalMs: 10_000 }));

    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });

    await act(async () => {
      result.current.applyRealtimeNotificationCreated({
        id: 202,
        type: 'offer.created',
        severity: 'info',
        title: 'Offer',
        body: 'New offer',
        entity_type: 'offer',
        entity_id: 22,
        link_url: '/requests/22',
        payload: {},
        read_at: null,
        created_at: '2026-05-18T10:00:00Z',
      });
    });

    await act(async () => {
      await result.current.markAllAsRead();
    });

    expect(result.current.hasUnread).toBe(false);
  });
});
