import { createWsTicket } from '@shared/api/wsTickets';

export type RealtimeConnectionState = 'idle' | 'connecting' | 'connected' | 'reconnecting';

type ErrorPayload = {
  code: string;
  message: string;
};

export type RealtimeEnvelope =
  | { type: 'connection.ready'; event_id: string; ts: string; data: { connection_id: string; user_id: string; transport: string; supported_event_types?: string[] } }
  | { type: 'notification.created'; event_id: string; ts: string; data: Record<string, unknown> }
  | { type: 'notification.read'; event_id: string; ts: string; data: Record<string, unknown> }
  | { type: 'notification.read_all'; event_id: string; ts: string; data: Record<string, unknown> }
  | { type: 'chat.message.created'; event_id: string; ts: string; data: Record<string, unknown> }
  | { type: 'system.toast'; event_id: string; ts: string; data: Record<string, unknown> }
  | { type: 'error'; event_id: string; ts: string; data: ErrorPayload }
  | { type: string; event_id: string; ts: string; data: Record<string, unknown> };

type EventListener = (event: RealtimeEnvelope) => void;
type StateListener = (state: RealtimeConnectionState) => void;

const buildSocketUrl = (ticket: string) => {
  const url = new URL(window.location.origin);
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  url.pathname = '/api/v1/ws/realtime';
  url.searchParams.set('ticket', ticket);
  return url.toString();
};

const createEventId = () => globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(16).slice(2)}`;

class RealtimeSocketClient {
  private socket: WebSocket | null = null;
  private shouldStayConnected = false;
  private eventListeners = new Set<EventListener>();
  private stateListeners = new Set<StateListener>();
  private reconnectTimerId: number | null = null;
  private reconnectAttempts = 0;
  private connectionState: RealtimeConnectionState = 'idle';
  private manualDisconnect = false;
  private ticketRequestPromise: Promise<string> | null = null;
  private openSocketPromise: Promise<void> | null = null;

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

  connect() {
    if (this.socket?.readyState === WebSocket.OPEN || this.socket?.readyState === WebSocket.CONNECTING) {
      return;
    }

    this.shouldStayConnected = true;
    this.manualDisconnect = false;
    this.clearReconnectTimer();
    this.ensureSocketOpen();
  }

  disconnect() {
    this.manualDisconnect = true;
    this.shouldStayConnected = false;
    this.ticketRequestPromise = null;
    this.openSocketPromise = null;
    this.clearReconnectTimer();
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    this.setState('idle');
  }

  private async getConnectionTicket(): Promise<string> {
    if (!this.ticketRequestPromise) {
      this.ticketRequestPromise = createWsTicket('realtime_ws')
        .then((payload) => payload.ticket)
        .finally(() => {
          this.ticketRequestPromise = null;
        });
    }
    return await this.ticketRequestPromise;
  }

  private ensureSocketOpen() {
    if (this.openSocketPromise) {
      return;
    }
    this.openSocketPromise = this.openSocket().finally(() => {
      this.openSocketPromise = null;
    });
  }

  private async openSocket() {
    if (!this.shouldStayConnected) {
      return;
    }

    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.setState(this.reconnectAttempts > 0 ? 'reconnecting' : 'connecting');

    let ticket: string;
    try {
      ticket = await this.getConnectionTicket();
    } catch {
      if (!this.manualDisconnect && this.shouldStayConnected) {
        this.scheduleReconnect();
      } else {
        this.setState('idle');
      }
      return;
    }

    if (!this.shouldStayConnected || this.manualDisconnect) {
      this.setState('idle');
      return;
    }

    const socket = new WebSocket(buildSocketUrl(ticket));
    this.socket = socket;

    socket.addEventListener('open', () => {
      this.reconnectAttempts = 0;
      this.setState('connected');
    });

    socket.addEventListener('message', (message) => {
      try {
        const payload = JSON.parse(message.data) as RealtimeEnvelope;
        this.emitEvent(payload);
      } catch {
        // Ignore malformed websocket messages.
      }
    });

    socket.addEventListener('close', (event) => {
      this.socket = null;

      if (event.code === 4401) {
        this.setState('idle');
        this.emitEvent({
          type: 'error',
          event_id: createEventId(),
          ts: new Date().toISOString(),
          data: {
            code: 'auth_failed',
            message: 'Auth failed',
          },
        });
        return;
      }

      if (this.manualDisconnect || !this.shouldStayConnected) {
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

  private scheduleReconnect() {
    this.clearReconnectTimer();
    this.reconnectAttempts += 1;
    this.setState('reconnecting');
    const delayMs = Math.min(1000 * 2 ** Math.min(this.reconnectAttempts, 4), 15000);
    this.reconnectTimerId = window.setTimeout(() => {
      this.reconnectTimerId = null;
      this.ensureSocketOpen();
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

  private emitEvent(event: RealtimeEnvelope) {
    this.eventListeners.forEach((listener) => listener(event));
  }
}

export const realtimeSocketClient = new RealtimeSocketClient();
