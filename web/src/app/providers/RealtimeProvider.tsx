import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
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
  const previousConnectionStateRef = useRef<RealtimeConnectionState>(realtimeSocketClient.getState());
  const syncInFlightRef = useRef<Promise<void> | null>(null);
  const lastSyncAtRef = useRef(0);

  const runNotificationsSync = useCallback(async () => {
      const now = Date.now();
      if (syncInFlightRef.current) {
        return await syncInFlightRef.current;
      }
      if (now - lastSyncAtRef.current < 1500) {
        return;
      }
      const task = syncNotifications()
        .catch(() => undefined)
        .finally(() => {
          lastSyncAtRef.current = Date.now();
          syncInFlightRef.current = null;
        });
      syncInFlightRef.current = task;
      await task;
    }, [syncNotifications]);

  useEffect(() => {
    const unsubscribe = realtimeSocketClient.onStateChange((nextState) => {
      const previousState = previousConnectionStateRef.current;
      previousConnectionStateRef.current = nextState;
      setConnectionState(nextState);
      if (previousState === 'reconnecting' && nextState === 'connected') {
        void runNotificationsSync();
      }
    });
    return unsubscribe;
  }, [runNotificationsSync]);

  useEffect(() => {
    const unsubscribe = realtimeSocketClient.onEvent((event) => {
      if (event.type === 'connection.ready') {
        void runNotificationsSync();
        return;
      }

      if (event.type === 'error' && event.data.code === 'auth_failed') {
        void refresh('ws_4401')
          .then((result) => {
            if (result.kind === 'terminal') {
              logout();
            }
          });
        return;
      }

      const createdEvent = parseNotificationCreatedEvent(event);
      if (!createdEvent) {
        if (event.type === 'notification.created') {
          console.warn('Ignore invalid notification.created realtime payload');
        }
        return;
      }

      applyRealtimeNotificationCreated(createdEvent.notification, createdEvent.hasUnread);
    });
    return unsubscribe;
  }, [applyRealtimeNotificationCreated, logout, refresh, runNotificationsSync]);

  useEffect(() => {
    if (status !== 'authenticated' || !session?.businessAccess) {
      realtimeSocketClient.disconnect();
      previousConnectionStateRef.current = 'idle';
      return;
    }
    realtimeSocketClient.connect();
  }, [session?.businessAccess, status]);

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
