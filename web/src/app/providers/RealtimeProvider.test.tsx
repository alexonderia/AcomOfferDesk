import { act, render, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { ReactNode } from 'react';
import { RealtimeProvider } from './RealtimeProvider';
import type { RealtimeConnectionState, RealtimeEnvelope } from '@shared/ws/realtimeSocket';

type MockAuthState = {
  session: { token: string; businessAccess: boolean } | null;
  status: string;
  refresh: any;
  logout: any;
};

let authState: MockAuthState = {
  session: { token: 'token', businessAccess: true },
  status: 'authenticated',
  refresh: vi.fn().mockResolvedValue(true),
  logout: vi.fn(),
};

const applyRealtimeNotificationCreatedMock = vi.fn();
const syncNotificationsMock = vi.fn().mockResolvedValue(undefined);

const connectMock = vi.fn();
const disconnectMock = vi.fn();
const onEventListeners = new Set<Function>();
const onStateListeners = new Set<Function>();
let currentState: RealtimeConnectionState = 'idle';

const emitRealtimeEvent = (event: RealtimeEnvelope) => {
  onEventListeners.forEach((listener) => listener(event));
};

const emitRealtimeState = (state: RealtimeConnectionState) => {
  currentState = state;
  onStateListeners.forEach((listener) => listener(state));
};

vi.mock('@app/providers/AuthProvider', () => ({
  useAuth: () => authState,
}));

vi.mock('@features/notifications/model/NotificationsContext', () => ({
  useNotificationsState: () => ({
    applyRealtimeNotificationCreated: applyRealtimeNotificationCreatedMock,
    syncNotifications: syncNotificationsMock,
  }),
}));

vi.mock('@shared/ws/realtimeSocket', () => ({
  realtimeSocketClient: {
    getState: () => currentState,
    connect: (...args: unknown[]) => connectMock(...args),
    disconnect: (...args: unknown[]) => disconnectMock(...args),
    onEvent: (listener: any) => {
      onEventListeners.add(listener);
      return () => onEventListeners.delete(listener);
    },
    onStateChange: (listener: any) => {
      onStateListeners.add(listener);
      listener(currentState);
      return () => onStateListeners.delete(listener);
    },
  },
}));

const Wrapper = ({ children }: { children: ReactNode }) => <RealtimeProvider>{children}</RealtimeProvider>;

describe('RealtimeProvider', () => {
  beforeEach(() => {
    authState = {
      session: { token: 'token', businessAccess: true },
      status: 'authenticated',
      refresh: vi.fn().mockResolvedValue(true),
      logout: vi.fn(),
    };
    currentState = 'idle';
    connectMock.mockReset();
    disconnectMock.mockReset();
    applyRealtimeNotificationCreatedMock.mockReset();
    syncNotificationsMock.mockReset();
    syncNotificationsMock.mockResolvedValue(undefined);
    onEventListeners.clear();
    onStateListeners.clear();
  });

  it('does not connect realtime socket when user is not authorized', () => {
    authState = {
      session: null,
      status: 'anonymous',
      refresh: vi.fn().mockResolvedValue(false),
      logout: vi.fn(),
    };

    render(<div />, { wrapper: Wrapper });

    expect(connectMock).not.toHaveBeenCalled();
    expect(disconnectMock).toHaveBeenCalledTimes(1);
  });

  it('applies notification.created event to notifications state', async () => {
    render(<div />, { wrapper: Wrapper });

    emitRealtimeEvent({
      type: 'notification.created',
      event_id: 'evt-1',
      ts: '2026-05-18T12:00:00Z',
      data: {
        notification: {
          id: 11,
          type: 'offer.created',
          severity: 'info',
          title: 'Offer created',
          body: 'Body',
          entity_type: 'offer',
          entity_id: 101,
          link_url: '/requests/101',
          payload: {},
          read_at: null,
          created_at: '2026-05-18T12:00:00Z',
        },
        has_unread: true,
      },
    });

    await waitFor(() => {
      expect(applyRealtimeNotificationCreatedMock).toHaveBeenCalledTimes(1);
    });
  });

  it('runs notifications sync on reconnect', async () => {
    render(<div />, { wrapper: Wrapper });

    await act(async () => {
      emitRealtimeState('reconnecting');
      emitRealtimeState('connected');
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(syncNotificationsMock).toHaveBeenCalledTimes(1);
    });
  });
});
