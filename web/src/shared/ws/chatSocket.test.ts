import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const createWsTicketMock = vi.fn();

vi.mock('@shared/api/wsTickets', () => ({
  createWsTicket: (...args: unknown[]) => createWsTicketMock(...args),
}));

class FakeWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  public readyState = FakeWebSocket.CONNECTING;
  public url: string;
  private listeners: Record<string, Function[]> = {};

  constructor(url: string) {
    this.url = url;
    this.readyState = FakeWebSocket.OPEN;
    queueMicrotask(() => this.dispatch('open'));
  }

  addEventListener(type: string, listener: Function) {
    this.listeners[type] = this.listeners[type] ?? [];
    this.listeners[type].push(listener);
  }

  send() {}

  close(code = 1000) {
    this.readyState = FakeWebSocket.CLOSED;
    this.dispatch('close', { code });
  }

  dispatch(type: string, event: any = {}) {
    for (const listener of this.listeners[type] ?? []) {
      listener(event);
    }
  }
}

describe('chatSocketClient', () => {
  beforeEach(() => {
    vi.resetModules();
    vi.useFakeTimers();
    createWsTicketMock.mockReset();
    (globalThis as any).WebSocket = FakeWebSocket;
  });

  afterEach(async () => {
    const { chatSocketClient } = await import('./chatSocket');
    const { realtimeSocketClient } = await import('./realtimeSocket');
    chatSocketClient.disconnect();
    realtimeSocketClient.disconnect();
    vi.useRealTimers();
  });

  it('uses realtime_ws ticket in URL and does not include token', async () => {
    createWsTicketMock.mockResolvedValueOnce({
      ticket: 'ticket-1',
      expires_in: 30,
      expires_at: '2026-01-01T00:00:00Z',
    });
    const { chatSocketClient } = await import('./chatSocket');
    const { realtimeSocketClient } = await import('./realtimeSocket');

    chatSocketClient.connect();
    await vi.runAllTimersAsync();

    const ws = (realtimeSocketClient as any).socket as FakeWebSocket;
    expect(createWsTicketMock).toHaveBeenCalledWith('realtime_ws');
    expect(createWsTicketMock).not.toHaveBeenCalledWith('chat_ws' as any);
    expect(ws.url).toContain('/api/v1/ws/realtime');
    expect(ws.url).not.toContain('/api/v1/ws/chat');
    expect(ws.url).toContain('ticket=ticket-1');
    expect(ws.url).not.toContain('token=');
    expect(ws.url).not.toContain('access_token');
  });

  it('requests new ticket on reconnect', async () => {
    createWsTicketMock
      .mockResolvedValueOnce({
        ticket: 'ticket-1',
        expires_in: 30,
        expires_at: '2026-01-01T00:00:00Z',
      })
      .mockResolvedValueOnce({
        ticket: 'ticket-2',
        expires_in: 30,
        expires_at: '2026-01-01T00:00:05Z',
      });
    const { chatSocketClient } = await import('./chatSocket');
    const { realtimeSocketClient } = await import('./realtimeSocket');

    chatSocketClient.connect();
    await vi.runAllTimersAsync();

    const first = (realtimeSocketClient as any).socket as FakeWebSocket;
    first.close(1006);
    await vi.advanceTimersByTimeAsync(2000);
    await vi.runAllTimersAsync();

    const second = (realtimeSocketClient as any).socket as FakeWebSocket;
    expect(createWsTicketMock).toHaveBeenCalledTimes(2);
    expect(second.url).toContain('ticket=ticket-2');
  });

  it('maps canonical chat.* events to legacy envelope for temporary UI compatibility', async () => {
    createWsTicketMock.mockResolvedValueOnce({
      ticket: 'ticket-compat',
      expires_in: 30,
      expires_at: '2026-01-01T00:00:00Z',
    });
    const { chatSocketClient } = await import('./chatSocket');
    const { realtimeSocketClient } = await import('./realtimeSocket');
    const receivedEvents: Array<{ type: string }> = [];

    const unsubscribe = chatSocketClient.onEvent((event) => {
      receivedEvents.push(event as { type: string });
    });

    chatSocketClient.connect();
    await vi.runAllTimersAsync();

    const ws = (realtimeSocketClient as any).socket as FakeWebSocket;
    ws.dispatch('message', {
      data: JSON.stringify({
        type: 'chat.message.created',
        event_id: 'evt-1',
        ts: '2026-05-18T12:00:00Z',
        data: { chat_id: 10, message: { id: 101 } },
      }),
    });

    unsubscribe();

    expect(receivedEvents.some((event) => event.type === 'message.created')).toBe(true);
  });
});
