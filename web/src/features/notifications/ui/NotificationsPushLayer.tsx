import { useCallback, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useSnackbar } from 'notistack';
import { useAuth } from '@app/providers/AuthProvider';
import { useRealtime } from '@app/providers/RealtimeProvider';
import { useNotificationsState } from '../model/NotificationsContext';
import {
  NOTIFICATION_PUSH_AUTOCLOSE_MS,
  NOTIFICATION_PUSH_BURST_THRESHOLD,
  NOTIFICATION_PUSH_ERROR_AUTOCLOSE_MS,
} from '../model/constants';
import { isNotificationForCurrentOpenChat } from '../model/isNotificationForCurrentOpenChat';
import { parseNotificationCreatedEvent } from '../model/realtimeNotificationEvent';
import { resolveNotificationLink } from '../model/resolveNotificationLink';
import type { Notification } from '../model/types';
import { NotificationPushToast } from './NotificationPushToast';

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
    title: `РЈ РІР°СЃ ${count} РЅРѕРІС‹С… СѓРІРµРґРѕРјР»РµРЅРёР№`,
    body: latest?.title ?? 'РћС‚РєСЂРѕР№С‚Рµ С†РµРЅС‚СЂ СѓРІРµРґРѕРјР»РµРЅРёР№, С‡С‚РѕР±С‹ РїРѕСЃРјРѕС‚СЂРµС‚СЊ РґРµС‚Р°Р»Рё.',
    created_at: latest?.created_at ?? new Date().toISOString(),
  };
};

const PUSH_BURST_WINDOW_MS = 350;

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

      if (orderedNotifications.length >= NOTIFICATION_PUSH_BURST_THRESHOLD) {
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
