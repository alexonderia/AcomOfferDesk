import {
  realtimeSocketClient,
  type RealtimeConnectionState,
  type RealtimeEnvelope,
} from './realtimeSocket';

export type { RealtimeConnectionState };

type AckPayload = {
  event_type: string;
  chat_id?: number;
  message_id?: number;
  updated_count?: number;
  last_read_message_id?: number | null;
};

type ErrorPayload = {
  code: string;
  message: string;
};

export type ChatRealtimeEnvelope =
  | {
      type: 'connection.ready';
      event_id: string;
      ts: string;
      request_id?: string | null;
      data: { connection_id: string; user_id: string; transport: string; supported_event_types?: string[] };
    }
  | {
      type: 'chat.sync';
      event_id: string;
      ts: string;
      request_id?: string | null;
      data: {
        chat_id: number;
        last_message_id: number | null;
        last_read_message_id: number | null;
        last_read_at: string | null;
        is_muted: boolean;
        is_archived: boolean;
        resync_required: boolean;
      };
    }
  | { type: 'chat.unsubscribed'; event_id: string; ts: string; request_id?: string | null; data: { chat_id: number } }
  | { type: 'message.created'; event_id: string; ts: string; request_id?: string | null; data: { chat_id: number; message: unknown } }
  | {
      type: 'message.delivered';
      event_id: string;
      ts: string;
      request_id?: string | null;
      data: { chat_id: number; user_id: string; message_ids: number[] };
    }
  | {
      type: 'message.read';
      event_id: string;
      ts: string;
      request_id?: string | null;
      data: {
        chat_id: number;
        user_id: string;
        user_full_name?: string | null;
        message_ids: number[];
        last_read_message_id: number | null;
      };
    }
  | { type: 'typing.start'; event_id: string; ts: string; request_id?: string | null; data: { chat_id: number; user_id: string } }
  | { type: 'typing.stop'; event_id: string; ts: string; request_id?: string | null; data: { chat_id: number; user_id: string } }
  | { type: 'ack'; event_id: string; ts: string; request_id?: string | null; data: AckPayload }
  | { type: 'error'; event_id: string; ts: string; request_id?: string | null; data: ErrorPayload };

type EventListener = (event: ChatRealtimeEnvelope) => void;
type StateListener = (state: RealtimeConnectionState) => void;

const mapRealtimeEventToChatEnvelope = (
  event: RealtimeEnvelope
): ChatRealtimeEnvelope | null => {
  if (event.type === 'connection.ready' || event.type === 'chat.sync' || event.type === 'chat.unsubscribed' || event.type === 'ack' || event.type === 'error') {
    return event as ChatRealtimeEnvelope;
  }

  if (event.type === 'message.created' || event.type === 'chat.message.created') {
    return {
      ...event,
      type: 'message.created',
    } as ChatRealtimeEnvelope;
  }

  if (event.type === 'message.delivered' || event.type === 'chat.message.delivered') {
    return {
      ...event,
      type: 'message.delivered',
    } as ChatRealtimeEnvelope;
  }

  if (event.type === 'message.read' || event.type === 'chat.message.read') {
    return {
      ...event,
      type: 'message.read',
    } as ChatRealtimeEnvelope;
  }

  if (event.type === 'typing.start' || event.type === 'chat.typing.started') {
    return {
      ...event,
      type: 'typing.start',
    } as ChatRealtimeEnvelope;
  }

  if (event.type === 'typing.stop' || event.type === 'chat.typing.stopped') {
    return {
      ...event,
      type: 'typing.stop',
    } as ChatRealtimeEnvelope;
  }

  return null;
};

class ChatSocketClient {
  getState() {
    return realtimeSocketClient.getState();
  }

  onEvent(listener: EventListener) {
    return realtimeSocketClient.onEvent((event) => {
      const mapped = mapRealtimeEventToChatEnvelope(event);
      if (!mapped) {
        return;
      }
      listener(mapped);
    });
  }

  onStateChange(listener: StateListener) {
    return realtimeSocketClient.onStateChange(listener);
  }

  connect() {
    realtimeSocketClient.connect();
  }

  disconnect() {
    realtimeSocketClient.disconnect();
  }

  subscribe(chatId: number) {
    realtimeSocketClient.subscribeChat(chatId);
  }

  unsubscribe(chatId: number) {
    realtimeSocketClient.unsubscribeChat(chatId);
  }

  sendMessage(chatId: number, text: string, files: Array<{ file_id: number; upload_token: string }>) {
    return realtimeSocketClient.sendChatMessage(chatId, text, files);
  }

  markRead(chatId: number, params: { messageIds?: number[]; upToMessageId?: number | null }) {
    return realtimeSocketClient.markChatRead(chatId, params);
  }

  syncChat(chatId: number, lastKnownMessageId?: number | null) {
    return realtimeSocketClient.syncChat(chatId, lastKnownMessageId);
  }

  typingStart(chatId: number) {
    return realtimeSocketClient.startTyping(chatId);
  }

  typingStop(chatId: number) {
    return realtimeSocketClient.stopTyping(chatId);
  }
}

export const chatSocketClient = new ChatSocketClient();
