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

describe('realtimeSocketClient', () => {
  beforeEach(() => {
    vi.resetModules();
    vi.useFakeTimers();
    createWsTicketMock.mockReset();
    (globalThis as any).WebSocket = FakeWebSocket;
  });

  afterEach(async () => {
    const { realtimeSocketClient } = await import('./realtimeSocket');
    realtimeSocketClient.disconnect();
    vi.useRealTimers();
  });

  it('uses realtime_ws ticket in URL and does not include token', async () => {
    createWsTicketMock.mockResolvedValueOnce({ ticket: 'rt-ticket-1', expires_in: 30, expires_at: '2026-01-01T00:00:00Z' });
    const { realtimeSocketClient } = await import('./realtimeSocket');

    realtimeSocketClient.connect();
    await vi.runAllTimersAsync();

    const ws = (realtimeSocketClient as any).socket as FakeWebSocket;
    expect(createWsTicketMock).toHaveBeenCalledWith('realtime_ws');
    expect(ws.url).toContain('/api/v1/ws/realtime');
    expect(ws.url).not.toContain('/api/v1/ws/chat');
    expect(ws.url).toContain('ticket=rt-ticket-1');
    expect(ws.url).not.toContain('token=');
    expect(ws.url).not.toContain('access_token');
  });

  it('requests a new realtime ticket on reconnect', async () => {
    createWsTicketMock
      .mockResolvedValueOnce({ ticket: 'rt-ticket-1', expires_in: 30, expires_at: '2026-01-01T00:00:00Z' })
      .mockResolvedValueOnce({ ticket: 'rt-ticket-2', expires_in: 30, expires_at: '2026-01-01T00:00:05Z' });
    const { realtimeSocketClient } = await import('./realtimeSocket');

    realtimeSocketClient.connect();
    await vi.runAllTimersAsync();

    const first = (realtimeSocketClient as any).socket as FakeWebSocket;
    first.close(1006);

    await vi.advanceTimersByTimeAsync(2000);
    await vi.runAllTimersAsync();

    const second = (realtimeSocketClient as any).socket as FakeWebSocket;
    expect(createWsTicketMock).toHaveBeenCalledTimes(2);
    expect(second.url).toContain('ticket=rt-ticket-2');
  });

  it('deduplicates connect calls and opens only one websocket', async () => {
    createWsTicketMock.mockResolvedValueOnce({ ticket: 'rt-ticket-1', expires_in: 30, expires_at: '2026-01-01T00:00:00Z' });
    const { realtimeSocketClient } = await import('./realtimeSocket');

    realtimeSocketClient.connect();
    realtimeSocketClient.connect();
    realtimeSocketClient.connect();
    await vi.runAllTimersAsync();

    expect(createWsTicketMock).toHaveBeenCalledTimes(1);
  });

  it('rejects pending websocket requests on disconnect', async () => {
    createWsTicketMock.mockResolvedValueOnce({ ticket: 'rt-ticket-1', expires_in: 30, expires_at: '2026-01-01T00:00:00Z' });
    const { realtimeSocketClient } = await import('./realtimeSocket');

    realtimeSocketClient.connect();
    await vi.runAllTimersAsync();

    const pendingRequest = realtimeSocketClient.markChatRead(10, { messageIds: [1] });
    realtimeSocketClient.disconnect();

    await expect(pendingRequest).rejects.toThrow('Соединение с сервером уведомлений закрыто.');
  });
});
