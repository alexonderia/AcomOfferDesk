import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSnackbar } from 'notistack';
import { useAuth } from '@app/providers/AuthProvider';
import { useNotificationsState } from '../model/NotificationsContext';
import { resolveNotificationLink } from '../model/resolveNotificationLink';
import type { Notification } from '../model/types';
import { NotificationPushToast } from './NotificationPushToast';

const PUSH_AUTOCLOSE_MS = 5000;

const isUnread = (notification: Notification) => notification.read_at === null;

export const NotificationsPushLayer = () => {
  const navigate = useNavigate();
  const { closeSnackbar, enqueueSnackbar } = useSnackbar();
  const { isAuthenticated } = useAuth();
  const { unreadCount, loadNotifications, markOneAsRead } = useNotificationsState();
  const isBootstrappedRef = useRef(false);
  const previousUnreadRef = useRef(0);
  const shownUnreadIdsRef = useRef<Set<number>>(new Set());

  useEffect(() => {
    if (!isAuthenticated) {
      isBootstrappedRef.current = false;
      previousUnreadRef.current = 0;
      shownUnreadIdsRef.current = new Set();
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
  }, [isAuthenticated, loadNotifications, unreadCount]);

  useEffect(() => {
    if (!isAuthenticated || !isBootstrappedRef.current) {
      return;
    }

    const previousUnreadCount = previousUnreadRef.current;
    previousUnreadRef.current = unreadCount;

    if (unreadCount <= previousUnreadCount) {
      return;
    }

    let cancelled = false;

    const showFreshNotifications = async () => {
      try {
        const latestItems = await loadNotifications({ silent: true });
        if (cancelled) {
          return;
        }

        const unreadItems = latestItems.filter(isUnread);
        const freshUnreadItems = unreadItems
          .filter((item) => !shownUnreadIdsRef.current.has(item.id))
          .sort((left, right) => Date.parse(left.created_at) - Date.parse(right.created_at));

        freshUnreadItems.forEach((item) => {
          shownUnreadIdsRef.current.add(item.id);
          const snackbarKey = `notification-push-${item.id}`;
          enqueueSnackbar(item.title, {
            key: snackbarKey,
            persist: false,
            autoHideDuration: PUSH_AUTOCLOSE_MS,
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
        // Notification center has its own inline error state; avoid noisy global errors for background polling.
      }
    };

    void showFreshNotifications();

    return () => {
      cancelled = true;
    };
  }, [closeSnackbar, enqueueSnackbar, isAuthenticated, loadNotifications, markOneAsRead, navigate, unreadCount]);

  return null;
};
