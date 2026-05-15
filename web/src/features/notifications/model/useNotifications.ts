import { useCallback, useEffect, useRef, useState } from 'react';
import {
  getNotifications,
  getUnreadCount,
  markAllNotificationsRead,
  markNotificationRead,
} from '../api/notificationsApi';
import type { Notification } from './types';
import { NOTIFICATION_PAGE_SIZE, NOTIFICATION_UNREAD_POLLING_INTERVAL_MS } from './constants';

const DEFAULT_POLLING_INTERVAL_MS = NOTIFICATION_UNREAD_POLLING_INTERVAL_MS;

const hasSameNotificationItems = (left: Notification[], right: Notification[]) => {
  if (left.length !== right.length) {
    return false;
  }

  return left.every((item, index) => {
    const candidate = right[index];
    return (
      candidate &&
      item.id === candidate.id &&
      item.read_at === candidate.read_at &&
      item.created_at === candidate.created_at &&
      item.title === candidate.title &&
      item.body === candidate.body &&
      item.severity === candidate.severity
    );
  });
};

type LoadOptions = {
  silent?: boolean;
  append?: boolean;
  offset?: number;
  limit?: number;
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
  const [hasMore, setHasMore] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);

  const listLoadInFlightRef = useRef<Map<string, Promise<Notification[]>>>(new Map());
  const markingIdsRef = useRef<Set<number>>(new Set());

  const refreshUnreadCount = useCallback(async () => {
    if (!enabled) {
      return 0;
    }

    const result = await getUnreadCount();
    setUnreadCount((current) => (current === result.count ? current : result.count));
    return result.count;
  }, [enabled]);

  const loadNotifications = useCallback(
    async (options: LoadOptions = {}) => {
      if (!enabled) {
        return [] as Notification[];
      }

      const silent = options.silent ?? false;
      const append = options.append ?? false;
      const limit = options.limit ?? NOTIFICATION_PAGE_SIZE;
      const offset = options.offset ?? (append ? items.length : 0);
      const requestKey = `${offset}:${limit}:${append ? 'append' : 'replace'}`;

      const inFlight = listLoadInFlightRef.current.get(requestKey);
      if (inFlight) {
        return inFlight;
      }

      if (!silent) {
        if (append) {
          setIsLoadingMore(true);
        } else {
          setIsLoadingList(true);
        }
      }
      setListError(null);

      const requestPromise = (async () => {
        try {
          const response = await getNotifications({ limit, offset });

          setItems((current) => {
            if (!append) {
              return hasSameNotificationItems(current, response.items) ? current : response.items;
            }

            if (response.items.length === 0) {
              return current;
            }

            const existingIds = new Set(current.map((item) => item.id));
            const merged = [...current];
            response.items.forEach((item) => {
              if (!existingIds.has(item.id)) {
                merged.push(item);
              }
            });
            return merged;
          });

          setHasMore(response.items.length >= limit);
          setIsListLoaded(true);
          return response.items;
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Failed to load notifications';
          setListError(message);
          throw error;
        } finally {
          listLoadInFlightRef.current.delete(requestKey);
          if (!silent) {
            if (append) {
              setIsLoadingMore(false);
            } else {
              setIsLoadingList(false);
            }
          }
        }
      })();

      listLoadInFlightRef.current.set(requestKey, requestPromise);
      return requestPromise;
    },
    [enabled, items.length]
  );

  const loadMoreNotifications = useCallback(async () => {
    if (!enabled || !isListLoaded || !hasMore || isLoadingMore) {
      return [] as Notification[];
    }

    return loadNotifications({
      append: true,
      offset: items.length,
      limit: NOTIFICATION_PAGE_SIZE,
    });
  }, [enabled, hasMore, isListLoaded, isLoadingMore, items.length, loadNotifications]);

  const syncAfterMarkAction = useCallback(async () => {
    await Promise.all([
      refreshUnreadCount(),
      isListLoaded
        ? loadNotifications({
            silent: true,
            offset: 0,
            append: false,
            limit: NOTIFICATION_PAGE_SIZE,
          })
        : Promise.resolve([] as Notification[]),
    ]);
  }, [isListLoaded, loadNotifications, refreshUnreadCount]);

  const markOneAsRead = useCallback(
    async (notificationId: number) => {
      if (!enabled) {
        return;
      }
      if (markingIdsRef.current.has(notificationId)) {
        return;
      }

      setMarkingIds((current) => {
        const next = new Set(current);
        next.add(notificationId);
        markingIdsRef.current = next;
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
          markingIdsRef.current = next;
          return next;
        });
      }
    },
    [enabled, syncAfterMarkAction]
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
      markingIdsRef.current = new Set();
      setHasMore(true);
      setIsLoadingMore(false);
      listLoadInFlightRef.current.clear();
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
    hasMore,
    isLoadingMore,
    loadNotifications,
    loadMoreNotifications,
    refreshUnreadCount,
    markOneAsRead,
    markAllAsRead,
  };
};
