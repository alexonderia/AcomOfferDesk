import { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { useAuth } from './AuthProvider';
import {
  realtimeSocketClient,
  type RealtimeConnectionState,
  type RealtimeEnvelope,
} from '@shared/ws/realtimeSocket';
import { useNotificationsState } from '@features/notifications/model/NotificationsContext';
import { parseNotificationCreatedEvent } from '@features/notifications/model/realtimeNotificationEvent';

type RealtimeContextValue = {
  client: typeof realtimeSocketClient;
  connectionState: RealtimeConnectionState;
  onEvent: (listener: (event: RealtimeEnvelope) => void) => () => void;
};

const RealtimeContext = createContext<RealtimeContextValue | undefined>(undefined);

export const RealtimeProvider = ({ children }: { children: React.ReactNode }) => {
  const { session, status, refresh, logout } = useAuth();
  const { applyRealtimeNotificationCreated, syncNotifications } = useNotificationsState();
  const [connectionState, setConnectionState] = useState<RealtimeConnectionState>(
    realtimeSocketClient.getState()
  );
  const refreshAttemptInFlightRef = useRef(false);
  const previousConnectionStateRef = useRef<RealtimeConnectionState>(realtimeSocketClient.getState());

  useEffect(() => {
    const unsubscribe = realtimeSocketClient.onStateChange((nextState) => {
      const previousState = previousConnectionStateRef.current;
      previousConnectionStateRef.current = nextState;
      setConnectionState(nextState);
      if (previousState === 'reconnecting' && nextState === 'connected') {
        void syncNotifications().catch(() => undefined);
      }
    });
    return unsubscribe;
  }, [syncNotifications]);

  useEffect(() => {
    const unsubscribe = realtimeSocketClient.onEvent((event) => {
      if (event.type === 'error' && event.data.code === 'auth_failed') {
        if (refreshAttemptInFlightRef.current) {
          return;
        }
        refreshAttemptInFlightRef.current = true;
        void refresh('ws_4401')
          .then((ok: boolean) => {
            if (!ok) {
              logout();
            }
          })
          .finally(() => {
            refreshAttemptInFlightRef.current = false;
          });
        return;
      }

      const createdEvent = parseNotificationCreatedEvent(event);
      if (!createdEvent) {
        return;
      }

      applyRealtimeNotificationCreated(createdEvent.notification, createdEvent.hasUnread);
    });
    return unsubscribe;
  }, [applyRealtimeNotificationCreated, logout, refresh]);

  useEffect(() => {
    if (status === 'anonymous' || !session?.token || !session.businessAccess) {
      realtimeSocketClient.disconnect();
      previousConnectionStateRef.current = 'idle';
      return;
    }
    if (status === 'refreshing') {
      return;
    }
    realtimeSocketClient.connect();
  }, [session?.businessAccess, session?.token, status]);

  const value = useMemo<RealtimeContextValue>(
    () => ({
      client: realtimeSocketClient,
      connectionState,
      onEvent: (listener: (event: RealtimeEnvelope) => void) => realtimeSocketClient.onEvent(listener),
    }),
    [connectionState]
  );

  return <RealtimeContext.Provider value={value}>{children}</RealtimeContext.Provider>;
};

export const useRealtime = () => {
  const context = useContext(RealtimeContext);
  if (!context) {
    throw new Error('useRealtime must be used within RealtimeProvider');
  }
  return context;
};
