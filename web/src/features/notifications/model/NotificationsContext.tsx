import { createContext, useContext } from 'react';
import type { ReactNode } from 'react';
import { useAuth } from '@app/providers/AuthProvider';
import { useNotifications } from './useNotifications';
import { NOTIFICATION_UNREAD_POLLING_INTERVAL_MS } from './constants';

type NotificationsState = ReturnType<typeof useNotifications>;

const NotificationsContext = createContext<NotificationsState | null>(null);

type NotificationsProviderProps = {
  children: ReactNode;
};

export const NotificationsProvider = ({ children }: NotificationsProviderProps) => {
  const { isAuthenticated } = useAuth();
  const notificationsState = useNotifications({
    enabled: isAuthenticated,
    pollingIntervalMs: NOTIFICATION_UNREAD_POLLING_INTERVAL_MS,
  });

  return (
    <NotificationsContext.Provider value={notificationsState}>{children}</NotificationsContext.Provider>
  );
};

export const useNotificationsState = () => {
  const context = useContext(NotificationsContext);
  if (!context) {
    throw new Error('useNotificationsState must be used within NotificationsProvider');
  }
  return context;
};
