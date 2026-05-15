import { useCallback, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useSnackbar } from 'notistack';
import { useAuth } from '@app/providers/AuthProvider';
import { useNotificationsState } from '../model/NotificationsContext';
import {
  NOTIFICATION_PUSH_AUTOCLOSE_MS,
  NOTIFICATION_PUSH_BURST_THRESHOLD,
  NOTIFICATION_PUSH_ERROR_AUTOCLOSE_MS,
  NOTIFICATION_PUSH_REFRESH_THROTTLE_MS,
} from '../model/constants';
import { isNotificationForCurrentOpenChat } from '../model/isNotificationForCurrentOpenChat';
import { resolveNotificationLink } from '../model/resolveNotificationLink';
import type { Notification } from '../model/types';
import { NotificationPushToast } from './NotificationPushToast';

const isUnread = (notification: Notification) => notification.read_at === null;

const getPushAutoHideDuration = (notification: Pick<Notification, 'severity'>): number =>
  notification.severity === 'error' || notification.severity === 'warning'
    ? NOTIFICATION_PUSH_ERROR_AUTOCLOSE_MS
    : NOTIFICATION_PUSH_AUTOCLOSE_MS;

const isMobileViewport = () =>
  typeof window !== 'undefined' && window.matchMedia('(max-width: 600px)').matches;

const buildBatchSummaryNotification = (
  notifications: Notification[]
): Pick<Notification, 'type' | 'severity' | 'title' | 'body' | 'created_at'> => {
  const count = notifications.length;
  const latest = notifications[notifications.length - 1];

  return {
    type: 'system.warning',
    severity: count >= 6 ? 'warning' : 'info',
    title: `У вас ${count} новых уведомлений`,
    body: latest?.title ?? 'Откройте центр уведомлений, чтобы посмотреть детали.',
    created_at: latest?.created_at ?? new Date().toISOString(),
  };
};

export const NotificationsPushLayer = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { closeSnackbar, enqueueSnackbar } = useSnackbar();
  const { isAuthenticated } = useAuth();
  const { unreadCount, loadNotifications, markOneAsRead } = useNotificationsState();

  const isBootstrappedRef = useRef(false);
  const previousUnreadRef = useRef(0);
  const shownUnreadIdsRef = useRef<Set<number>>(new Set());
  const isPushRefreshInFlightRef = useRef(false);
  const hasPendingPushRefreshRef = useRef(false);
  const lastPushRefreshAtRef = useRef(0);
  const scheduledPushRefreshTimerRef = useRef<number | null>(null);

  const resetPushRefs = useCallback(() => {
    isBootstrappedRef.current = false;
    previousUnreadRef.current = 0;
    shownUnreadIdsRef.current = new Set();
    isPushRefreshInFlightRef.current = false;
    hasPendingPushRefreshRef.current = false;
    lastPushRefreshAtRef.current = 0;
    if (scheduledPushRefreshTimerRef.current !== null) {
      window.clearTimeout(scheduledPushRefreshTimerRef.current);
      scheduledPushRefreshTimerRef.current = null;
    }
  }, []);

  const runPushRefresh = useCallback(async () => {
    if (!isAuthenticated || !isBootstrappedRef.current) {
      return;
    }

    if (isPushRefreshInFlightRef.current) {
      hasPendingPushRefreshRef.current = true;
      return;
    }

    const now = Date.now();
    const msSinceLastRefresh = now - lastPushRefreshAtRef.current;
    const remainingThrottleMs = NOTIFICATION_PUSH_REFRESH_THROTTLE_MS - msSinceLastRefresh;

    if (remainingThrottleMs > 0) {
      if (scheduledPushRefreshTimerRef.current === null) {
        scheduledPushRefreshTimerRef.current = window.setTimeout(() => {
          scheduledPushRefreshTimerRef.current = null;
          void runPushRefresh();
        }, remainingThrottleMs);
      }
      return;
    }

    isPushRefreshInFlightRef.current = true;
    lastPushRefreshAtRef.current = Date.now();

    try {
      const latestItems = await loadNotifications({ silent: true });
      const unreadItems = latestItems.filter(isUnread);
      const freshUnreadItems: Notification[] = [];

      unreadItems.forEach((item) => {
        if (shownUnreadIdsRef.current.has(item.id)) {
          return;
        }

        if (item.type === 'message.created' && isNotificationForCurrentOpenChat(item, location)) {
          shownUnreadIdsRef.current.add(item.id);
          return;
        }

        shownUnreadIdsRef.current.add(item.id);
        freshUnreadItems.push(item);
      });

      if (freshUnreadItems.length === 0) {
        return;
      }

      const anchorOrigin = isMobileViewport()
        ? { vertical: 'bottom' as const, horizontal: 'center' as const }
        : { vertical: 'bottom' as const, horizontal: 'right' as const };

      const notificationsToShow = [...freshUnreadItems].sort(
        (left, right) => Date.parse(left.created_at) - Date.parse(right.created_at)
      );

      if (notificationsToShow.length >= NOTIFICATION_PUSH_BURST_THRESHOLD) {
        const summary = buildBatchSummaryNotification(notificationsToShow);
        const latestRoutePath = resolveNotificationLink(
          notificationsToShow[notificationsToShow.length - 1]?.link_url ?? null
        );
        const snackbarKey = `notification-push-batch-${notificationsToShow.map((item) => item.id).join('-')}`;
        enqueueSnackbar(summary.title, {
          key: snackbarKey,
          persist: false,
          autoHideDuration: getPushAutoHideDuration(summary),
          anchorOrigin,
          content: (key) => (
            <NotificationPushToast
              notification={summary}
              onClose={() => {
                closeSnackbar(key);
              }}
              onClick={() => {
                closeSnackbar(key);
                navigate(latestRoutePath ?? '/requests');
              }}
            />
          ),
        });
        return;
      }

      notificationsToShow.forEach((item) => {
        const snackbarKey = `notification-push-${item.id}`;
        enqueueSnackbar(item.title, {
          key: snackbarKey,
          persist: false,
          autoHideDuration: getPushAutoHideDuration(item),
          anchorOrigin,
          content: (key) => (
            <NotificationPushToast
              notification={item}
              onClose={() => {
                closeSnackbar(key);
              }}
              onClick={() => {
                closeSnackbar(key);
                void (async () => {
                  if (item.read_at === null) {
                    await markOneAsRead(item.id).catch(() => undefined);
                  }

                  const routePath = resolveNotificationLink(item.link_url);
                  if (routePath) {
                    navigate(routePath);
                  }
                })();
              }}
            />
          ),
        });
      });
    } catch {
      // Keep background push refresh silent. Notification center already has inline error state.
    } finally {
      isPushRefreshInFlightRef.current = false;
      if (hasPendingPushRefreshRef.current) {
        hasPendingPushRefreshRef.current = false;
        void runPushRefresh();
      }
    }
  }, [closeSnackbar, enqueueSnackbar, isAuthenticated, loadNotifications, location, markOneAsRead, navigate]);

  useEffect(() => {
    if (!isAuthenticated) {
      resetPushRefs();
      return;
    }

    if (isBootstrappedRef.current) {
      return;
    }

    let cancelled = false;

    const bootstrap = async () => {
      try {
        const initialItems = await loadNotifications({ silent: true });
        if (cancelled) {
          return;
        }

        const unreadItems = initialItems.filter(isUnread);
        shownUnreadIdsRef.current = new Set(unreadItems.map((item) => item.id));
        previousUnreadRef.current = Math.max(unreadCount, unreadItems.length);
        isBootstrappedRef.current = true;
      } catch {
        if (cancelled) {
          return;
        }
        previousUnreadRef.current = unreadCount;
        isBootstrappedRef.current = true;
      }
    };

    void bootstrap();

    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, loadNotifications, resetPushRefs, unreadCount]);

  useEffect(() => {
    if (!isAuthenticated || !isBootstrappedRef.current) {
      return;
    }

    const previousUnreadCount = previousUnreadRef.current;
    previousUnreadRef.current = unreadCount;

    if (unreadCount <= previousUnreadCount) {
      return;
    }

    void runPushRefresh();
  }, [isAuthenticated, runPushRefresh, unreadCount]);

  useEffect(() => () => {
    if (scheduledPushRefreshTimerRef.current !== null) {
      window.clearTimeout(scheduledPushRefreshTimerRef.current);
      scheduledPushRefreshTimerRef.current = null;
    }
  }, []);

  return null;
};
