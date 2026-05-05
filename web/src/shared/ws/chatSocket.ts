export type RealtimeConnectionState = 'idle' | 'connecting' | 'connected' | 'reconnecting';

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
  | { type: 'connection.ready'; event_id: string; ts: string; request_id?: string | null; data: { connection_id: string; user_id: string; transport: string } }
  | { type: 'chat.sync'; event_id: string; ts: string; request_id?: string | null; data: { chat_id: number; last_message_id: number | null; last_read_message_id: number | null; last_read_at: string | null; is_muted: boolean; is_archived: boolean; resync_required: boolean } }
  | { type: 'chat.unsubscribed'; event_id: string; ts: string; request_id?: string | null; data: { chat_id: number } }
  | { type: 'message.created'; event_id: string; ts: string; request_id?: string | null; data: { chat_id: number; message: unknown } }
  | { type: 'message.delivered'; event_id: string; ts: string; request_id?: string | null; data: { chat_id: number; user_id: string; message_ids: number[] } }
  | { type: 'message.read'; event_id: string; ts: string; request_id?: string | null; data: { chat_id: number; user_id: string; user_full_name?: string | null; message_ids: number[]; last_read_message_id: number | null } }
  | { type: 'typing.start'; event_id: string; ts: string; request_id?: string | null; data: { chat_id: number; user_id: string } }
  | { type: 'typing.stop'; event_id: string; ts: string; request_id?: string | null; data: { chat_id: number; user_id: string } }
  | { type: 'ack'; event_id: string; ts: string; request_id?: string | null; data: AckPayload }
  | { type: 'error'; event_id: string; ts: string; request_id?: string | null; data: ErrorPayload };

type EventListener = (event: ChatRealtimeEnvelope) => void;
type StateListener = (state: RealtimeConnectionState) => void;

type PendingRequest = {
  resolve: (data: AckPayload) => void;
  reject: (error: Error) => void;
  timeoutId: number;
};

const REQUEST_TIMEOUT_MS = 15000;

const buildSocketUrl = (token: string) => {
  const url = new URL(window.location.origin);
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  url.pathname = '/api/v1/ws/chat';
  url.searchParams.set('token', token);
  return url.toString();
};

const createRequestId = () => globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(16).slice(2)}`;
const createEventId = () => globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(16).slice(2)}`;

class ChatSocketClient {
  private socket: WebSocket | null = null;
  private token: string | null = null;
  private desiredChats = new Set<number>();
  private eventListeners = new Set<EventListener>();
  private stateListeners = new Set<StateListener>();
  private pendingRequests = new Map<string, PendingRequest>();
  private reconnectTimerId: number | null = null;
  private reconnectAttempts = 0;
  private connectionState: RealtimeConnectionState = 'idle';
  private manualDisconnect = false;

  getState() {
    return this.connectionState;
  }

  onEvent(listener: EventListener) {
    this.eventListeners.add(listener);
    return () => {
      this.eventListeners.delete(listener);
    };
  }

  onStateChange(listener: StateListener) {
    this.stateListeners.add(listener);
    listener(this.connectionState);
    return () => {
      this.stateListeners.delete(listener);
    };
  }

  connect(token: string) {
    if (!token) {
      this.disconnect();
      return;
    }

    if (this.token === token && (this.socket?.readyState === WebSocket.OPEN || this.socket?.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.token = token;
    this.manualDisconnect = false;
    this.clearReconnectTimer();
    this.openSocket();
  }

  disconnect() {
    this.manualDisconnect = true;
    this.token = null;
    this.desiredChats.clear();
    this.clearReconnectTimer();
    this.rejectPendingRequests('Соединение с чатом закрыто');
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    this.setState('idle');
  }

  subscribe(chatId: number) {
    this.desiredChats.add(chatId);
    if (this.connectionState === 'connected') {
      void this.sendRequest('chat.subscribe', { chat_id: chatId }).catch(() => undefined);
    }
  }

  unsubscribe(chatId: number) {
    this.desiredChats.delete(chatId);
    if (this.connectionState === 'connected') {
      void this.sendRequest('chat.unsubscribe', { chat_id: chatId }).catch(() => undefined);
    }
  }

  sendMessage(chatId: number, text: string, files: Array<{ file_id: number; upload_token: string }>) {
    return this.sendRequest('message.send', { chat_id: chatId, text, files });
  }

  markRead(chatId: number, params: { messageIds?: number[]; upToMessageId?: number | null }) {
    return this.sendRequest('message.read', {
      chat_id: chatId,
      message_ids: params.messageIds,
      up_to_message_id: params.upToMessageId ?? null
    });
  }

  syncChat(chatId: number, lastKnownMessageId?: number | null) {
    return this.sendRequest('chat.sync', {
      chat_id: chatId,
      last_known_message_id: lastKnownMessageId ?? null
    });
  }

  typingStart(chatId: number) {
    return this.sendRequest('typing.start', { chat_id: chatId });
  }

  typingStop(chatId: number) {
    return this.sendRequest('typing.stop', { chat_id: chatId });
  }

  private openSocket() {
    if (!this.token) {
      return;
    }

    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.setState(this.reconnectAttempts > 0 ? 'reconnecting' : 'connecting');
    const socket = new WebSocket(buildSocketUrl(this.token));
    this.socket = socket;

    socket.addEventListener('open', () => {
      this.reconnectAttempts = 0;
      this.setState('connected');
    });

    socket.addEventListener('message', (message) => {
      try {
        const payload = JSON.parse(message.data) as ChatRealtimeEnvelope;
        if (payload.type === 'ack' && payload.request_id) {
          this.resolvePendingRequest(payload.request_id, payload.data);
        }
        if (payload.type === 'error' && payload.request_id) {
          this.rejectPendingRequest(payload.request_id, payload.data.message);
        }
        if (payload.type === 'connection.ready') {
          for (const chatId of this.desiredChats) {
            void this.sendRequest('chat.subscribe', { chat_id: chatId }).catch(() => undefined);
          }
        }
        this.emitEvent(payload);
      } catch {
        // Ignore malformed websocket messages.
      }
    });

    socket.addEventListener('close', (event) => {
      this.socket = null;
      this.rejectPendingRequests('Соединение с чатом потеряно');

      if (event.code === 4401) {
        this.setState('idle');
        this.emitEvent({
          type: 'error',
          event_id: createEventId(),
          ts: new Date().toISOString(),
          data: {
            code: 'auth_failed',
            message: 'Auth failed'
          }
        });
        return;
      }

      if (this.manualDisconnect || !this.token) {
        this.setState('idle');
        return;
      }
      this.scheduleReconnect();
    });

    socket.addEventListener('error', () => {
      if (socket.readyState !== WebSocket.CLOSED) {
        socket.close();
      }
    });
  }

  private async sendRequest(type: string, data: Record<string, unknown>): Promise<AckPayload> {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      throw new Error('Соединение в реальном времени недоступно');
    }

    const requestId = createRequestId();
    const payload = JSON.stringify({
      type,
      request_id: requestId,
      data
    });

    return await new Promise<AckPayload>((resolve, reject) => {
      const timeoutId = window.setTimeout(() => {
        this.pendingRequests.delete(requestId);
        reject(new Error('Сервер не подтвердил WebSocket-запрос вовремя'));
      }, REQUEST_TIMEOUT_MS);

      this.pendingRequests.set(requestId, { resolve, reject, timeoutId });
      this.socket?.send(payload);
    });
  }

  private resolvePendingRequest(requestId: string, payload: AckPayload) {
    const pending = this.pendingRequests.get(requestId);
    if (!pending) {
      return;
    }
    window.clearTimeout(pending.timeoutId);
    this.pendingRequests.delete(requestId);
    pending.resolve(payload);
  }

  private rejectPendingRequest(requestId: string, message: string) {
    const pending = this.pendingRequests.get(requestId);
    if (!pending) {
      return;
    }
    window.clearTimeout(pending.timeoutId);
    this.pendingRequests.delete(requestId);
    pending.reject(new Error(message));
  }

  private rejectPendingRequests(message: string) {
    this.pendingRequests.forEach((pending, requestId) => {
      window.clearTimeout(pending.timeoutId);
      pending.reject(new Error(message));
      this.pendingRequests.delete(requestId);
    });
  }

  private scheduleReconnect() {
    this.clearReconnectTimer();
    this.reconnectAttempts += 1;
    this.setState('reconnecting');
    const delayMs = Math.min(1000 * 2 ** Math.min(this.reconnectAttempts, 4), 15000);
    this.reconnectTimerId = window.setTimeout(() => {
      this.reconnectTimerId = null;
      this.openSocket();
    }, delayMs);
  }

  private clearReconnectTimer() {
    if (this.reconnectTimerId !== null) {
      window.clearTimeout(this.reconnectTimerId);
      this.reconnectTimerId = null;
    }
  }

  private setState(nextState: RealtimeConnectionState) {
    this.connectionState = nextState;
    this.stateListeners.forEach((listener) => listener(nextState));
  }

  private emitEvent(event: ChatRealtimeEnvelope) {
    this.eventListeners.forEach((listener) => listener(event));
  }
}

export const chatSocketClient = new ChatSocketClient();
