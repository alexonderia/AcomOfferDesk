import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import {
  chatSocketClient,
  type ChatRealtimeEnvelope,
  type RealtimeConnectionState,
} from '@shared/ws/chatSocket';

type ChatRealtimeContextValue = {
  client: typeof chatSocketClient;
  connectionState: RealtimeConnectionState;
  onEvent: (listener: (event: ChatRealtimeEnvelope) => void) => () => void;
};

const ChatRealtimeContext = createContext<ChatRealtimeContextValue | undefined>(undefined);

export const ChatRealtimeProvider = ({ children }: { children: React.ReactNode }) => {
  const [connectionState, setConnectionState] = useState<RealtimeConnectionState>(
    chatSocketClient.getState()
  );

  useEffect(() => {
    const unsubscribe = chatSocketClient.onStateChange(setConnectionState);
    return unsubscribe;
  }, []);

  const value = useMemo<ChatRealtimeContextValue>(
    () => ({
      client: chatSocketClient,
      connectionState,
      onEvent: (listener: (event: ChatRealtimeEnvelope) => void) =>
        chatSocketClient.onEvent(listener),
    }),
    [connectionState]
  );

  return (
    <ChatRealtimeContext.Provider value={value}>{children}</ChatRealtimeContext.Provider>
  );
};

export const useChatRealtime = () => {
  const context = useContext(ChatRealtimeContext);
  if (!context) {
    throw new Error('useChatRealtime must be used within ChatRealtimeProvider');
  }
  return context;
};
