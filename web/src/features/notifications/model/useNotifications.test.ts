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

  it('polls unread count by interval when enabled', async () => {
    getUnreadCountMock.mockResolvedValue({ count: 5 });

    const { result } = renderHook(() =>
      useNotifications({ enabled: true, pollingIntervalMs: 1_000 })
    );

    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(result.current.unreadCount).toBe(5);

    await act(async () => {
      vi.advanceTimersByTime(2_100);
      await Promise.resolve();
    });

    expect(getUnreadCountMock).toHaveBeenCalledTimes(3);
  });
});
