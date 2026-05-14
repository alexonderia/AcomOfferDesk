import { useCallback, useEffect, useState } from 'react';
import {
  getNotifications,
  getUnreadCount,
  markAllNotificationsRead,
  markNotificationRead,
} from '../api/notificationsApi';
import type { Notification } from './types';

const DEFAULT_POLLING_INTERVAL_MS = 25_000;

type LoadOptions = {
  silent?: boolean;
};

type UseNotificationsOptions = {
  enabled: boolean;
  pollingIntervalMs?: number;
};

export const useNotifications = ({
  enabled,
  pollingIntervalMs = DEFAULT_POLLING_INTERVAL_MS,
}: UseNotificationsOptions) => {
  const [items, setItems] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoadingList, setIsLoadingList] = useState(false);
  const [isListLoaded, setIsListLoaded] = useState(false);
  const [listError, setListError] = useState<string | null>(null);
  const [isMarkAllPending, setIsMarkAllPending] = useState(false);
  const [markingIds, setMarkingIds] = useState<Set<number>>(new Set());

  const refreshUnreadCount = useCallback(async () => {
    if (!enabled) {
      return 0;
    }

    const result = await getUnreadCount();
    setUnreadCount(result.count);
    return result.count;
  }, [enabled]);

  const loadNotifications = useCallback(
    async (options: LoadOptions = {}) => {
      if (!enabled) {
        return [] as Notification[];
      }

      const silent = options.silent ?? false;
      if (!silent) {
        setIsLoadingList(true);
      }
      setListError(null);

      try {
        const response = await getNotifications({ limit: 50, offset: 0 });
        setItems(response.items);
        setIsListLoaded(true);
        return response.items;
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Не удалось загрузить уведомления';
        setListError(message);
        throw error;
      } finally {
        if (!silent) {
          setIsLoadingList(false);
        }
      }
    },
    [enabled]
  );

  const syncAfterMarkAction = useCallback(async () => {
    await Promise.all([
      refreshUnreadCount(),
      isListLoaded ? loadNotifications({ silent: true }) : Promise.resolve([] as Notification[]),
    ]);
  }, [isListLoaded, loadNotifications, refreshUnreadCount]);

  const markOneAsRead = useCallback(
    async (notificationId: number) => {
      if (!enabled) {
        return;
      }
      if (markingIds.has(notificationId)) {
        return;
      }

      setMarkingIds((current) => {
        const next = new Set(current);
        next.add(notificationId);
        return next;
      });

      try {
        const response = await markNotificationRead(notificationId);
        setItems((current) =>
          current.map((item) =>
            item.id === notificationId ? { ...item, read_at: response.read_at } : item
          )
        );
        await syncAfterMarkAction();
      } finally {
        setMarkingIds((current) => {
          const next = new Set(current);
          next.delete(notificationId);
          return next;
        });
      }
    },
    [enabled, markingIds, syncAfterMarkAction]
  );

  const markAllAsRead = useCallback(async () => {
    if (!enabled || unreadCount <= 0 || isMarkAllPending) {
      return 0;
    }

    setIsMarkAllPending(true);
    try {
      const response = await markAllNotificationsRead();
      await syncAfterMarkAction();
      return response.updated_count;
    } finally {
      setIsMarkAllPending(false);
    }
  }, [enabled, isMarkAllPending, syncAfterMarkAction, unreadCount]);

  useEffect(() => {
    if (!enabled) {
      setUnreadCount(0);
      setItems([]);
      setIsListLoaded(false);
      setListError(null);
      setIsLoadingList(false);
      setIsMarkAllPending(false);
      setMarkingIds(new Set());
      return;
    }

    void refreshUnreadCount().catch(() => undefined);
    const intervalId = window.setInterval(() => {
      void refreshUnreadCount().catch(() => undefined);
    }, pollingIntervalMs);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [enabled, pollingIntervalMs, refreshUnreadCount]);

  return {
    items,
    unreadCount,
    isLoadingList,
    isListLoaded,
    listError,
    isMarkAllPending,
    markingIds,
    loadNotifications,
    refreshUnreadCount,
    markOneAsRead,
    markAllAsRead,
  };
};
