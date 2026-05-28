import { useCallback, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useSnackbar } from 'notistack';
import { useAuth } from '@app/providers/AuthProvider';
import { useRealtime } from '@app/providers/RealtimeProvider';
import { useNotificationsState } from '../model/NotificationsContext';
import {
  NOTIFICATION_PUSH_BURST_THRESHOLD,
} from '../model/constants';
import { isNotificationForCurrentOpenChat } from '../model/isNotificationForCurrentOpenChat';
import { parseNotificationCreatedEvent } from '../model/realtimeNotificationEvent';
import { resolveNotificationLink } from '../model/resolveNotificationLink';
import type { Notification } from '../model/types';
import { NotificationPushToast } from './NotificationPushToast';
import { getBusinessToastAutoHideDuration } from '@shared/ui/toasts';

const getPushAutoHideDuration = (notification: Pick<Notification, 'severity'>): number =>
  getBusinessToastAutoHideDuration(notification.severity);

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
    body: latest?.title ?? 'Откройте центр уведомлений, чтобы посмотреть подробности.',
    created_at: latest?.created_at ?? new Date().toISOString(),
  };
};

const PUSH_BURST_WINDOW_MS = 600;

const toPushSignature = (notification: Notification) =>
  `${notification.type}|${notification.title}|${notification.body}|${notification.link_url ?? ''}`;

const hasDuplicateSignatures = (notifications: Notification[]) => {
  const signatures = new Set<string>();
  for (const notification of notifications) {
    const signature = toPushSignature(notification);
    if (signatures.has(signature)) {
      return true;
    }
    signatures.add(signature);
  }
  return false;
};

export const NotificationsPushLayer = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { closeSnackbar, enqueueSnackbar } = useSnackbar();
  const { isAuthenticated } = useAuth();
  const { onEvent } = useRealtime();
  const { markOneAsRead } = useNotificationsState();

  const shownNotificationIdsRef = useRef<Set<number>>(new Set());
  const burstQueueRef = useRef<Notification[]>([]);
  const burstTimerRef = useRef<number | null>(null);

  const resetPushRefs = useCallback(() => {
    shownNotificationIdsRef.current = new Set();
    burstQueueRef.current = [];
    if (burstTimerRef.current !== null) {
      window.clearTimeout(burstTimerRef.current);
      burstTimerRef.current = null;
    }
  }, []);

  const showNotifications = useCallback(
    (notifications: Notification[]) => {
      if (notifications.length === 0) {
        return;
      }

      const anchorOrigin = isMobileViewport()
        ? { vertical: 'bottom' as const, horizontal: 'center' as const }
        : { vertical: 'bottom' as const, horizontal: 'right' as const };

      const orderedNotifications = [...notifications].sort(
        (left, right) => Date.parse(left.created_at) - Date.parse(right.created_at)
      );

      const shouldShowSummary =
        orderedNotifications.length >= NOTIFICATION_PUSH_BURST_THRESHOLD ||
        hasDuplicateSignatures(orderedNotifications);

      if (shouldShowSummary) {
        const summary = buildBatchSummaryNotification(orderedNotifications);
        const latestRoutePath = resolveNotificationLink(
          orderedNotifications[orderedNotifications.length - 1]?.link_url ?? null
        );
        const snackbarKey = `notification-push-batch-${orderedNotifications.map((item) => item.id).join('-')}`;
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

      orderedNotifications.forEach((notification) => {
        const snackbarKey = `notification-push-${notification.id}`;
        enqueueSnackbar(notification.title, {
          key: snackbarKey,
          persist: false,
          autoHideDuration: getPushAutoHideDuration(notification),
          anchorOrigin,
          content: (key) => (
            <NotificationPushToast
              notification={notification}
              onClose={() => {
                closeSnackbar(key);
              }}
              onClick={() => {
                closeSnackbar(key);
                void (async () => {
                  if (notification.read_at === null) {
                    await markOneAsRead(notification.id).catch(() => undefined);
                  }

                  const routePath = resolveNotificationLink(notification.link_url);
                  if (routePath) {
                    navigate(routePath);
                  }
                })();
              }}
            />
          ),
        });
      });
    },
    [closeSnackbar, enqueueSnackbar, markOneAsRead, navigate]
  );

  const flushBurstQueue = useCallback(() => {
    burstTimerRef.current = null;
    const queued = burstQueueRef.current;
    burstQueueRef.current = [];
    showNotifications(queued);
  }, [showNotifications]);

  const queueNotification = useCallback(
    (notification: Notification) => {
      burstQueueRef.current.push(notification);
      if (burstTimerRef.current !== null) {
        return;
      }
      burstTimerRef.current = window.setTimeout(flushBurstQueue, PUSH_BURST_WINDOW_MS);
    },
    [flushBurstQueue]
  );

  useEffect(() => {
    if (!isAuthenticated) {
      resetPushRefs();
      return;
    }

    const unsubscribe = onEvent((event) => {
      const createdEvent = parseNotificationCreatedEvent(event);
      if (!createdEvent) {
        return;
      }

      const notification = createdEvent.notification;
      if (shownNotificationIdsRef.current.has(notification.id)) {
        return;
      }
      shownNotificationIdsRef.current.add(notification.id);

      if (notification.type === 'message.created' && isNotificationForCurrentOpenChat(notification, location)) {
        return;
      }

      queueNotification(notification);
    });

    return unsubscribe;
  }, [isAuthenticated, location, onEvent, queueNotification, resetPushRefs]);

  useEffect(
    () => () => {
      if (burstTimerRef.current !== null) {
        window.clearTimeout(burstTimerRef.current);
        burstTimerRef.current = null;
      }
    },
    []
  );

  return null;
};
