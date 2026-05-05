import { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { useAuth } from './AuthProvider';
import { chatSocketClient, type ChatRealtimeEnvelope, type RealtimeConnectionState } from '@shared/ws/chatSocket';

type ChatRealtimeContextValue = {
  client: typeof chatSocketClient;
  connectionState: RealtimeConnectionState;
  onEvent: (listener: (event: ChatRealtimeEnvelope) => void) => () => void;
};

const ChatRealtimeContext = createContext<ChatRealtimeContextValue | undefined>(undefined);

export const ChatRealtimeProvider = ({ children }: { children: React.ReactNode }) => {
  const { session, status, refresh, logout } = useAuth();
  const [connectionState, setConnectionState] = useState<RealtimeConnectionState>(chatSocketClient.getState());
  const refreshAttemptInFlightRef = useRef(false);

  useEffect(() => {
    const unsubscribe = chatSocketClient.onStateChange(setConnectionState);
    return unsubscribe;
  }, []);

  useEffect(() => {
    const unsubscribe = chatSocketClient.onEvent((event) => {
      if (event.type !== 'error' || event.data.code !== 'auth_failed') {
        return;
      }
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
    });

    return unsubscribe;
  }, [logout, refresh]);

  useEffect(() => {
    if (status === 'anonymous' || !session?.token || !session.businessAccess) {
      chatSocketClient.disconnect();
      return;
    }
    if (status === 'refreshing') {
      return;
    }
    chatSocketClient.connect(session.token);
  }, [session?.token, status]);

  const value = useMemo<ChatRealtimeContextValue>(
    () => ({
      client: chatSocketClient,
      connectionState,
      onEvent: (listener: (event: ChatRealtimeEnvelope) => void) => chatSocketClient.onEvent(listener)
    }),
    [connectionState]
  );

  return <ChatRealtimeContext.Provider value={value}>{children}</ChatRealtimeContext.Provider>;
};

export const useChatRealtime = () => {
  const context = useContext(ChatRealtimeContext);
  if (!context) {
    throw new Error('useChatRealtime must be used within ChatRealtimeProvider');
  }
  return context;
};
