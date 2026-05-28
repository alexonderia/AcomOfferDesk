import { act, fireEvent, render, screen } from '@testing-library/react';
import type { ReactElement } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { NotificationsPushLayer } from './NotificationsPushLayer';
import type { Notification } from '../model/types';

const enqueueSnackbarMock = vi.fn();
const closeSnackbarMock = vi.fn();
const navigateMock = vi.fn();

let currentPathname = '/requests';
let isAuthenticated = true;
let realtimeListener: Function | null = null;

const notificationsState = {
  markOneAsRead: vi.fn(),
};

vi.mock('../model/constants', () => ({
  NOTIFICATION_PUSH_AUTOCLOSE_MS: 10_000,
  NOTIFICATION_PUSH_ERROR_AUTOCLOSE_MS: 14_000,
  NOTIFICATION_PUSH_BURST_THRESHOLD: 3,
}));

vi.mock('@app/providers/AuthProvider', () => ({
  useAuth: () => ({
    isAuthenticated,
  }),
}));

vi.mock('@app/providers/RealtimeProvider', () => ({
  useRealtime: () => ({
    onEvent: (listener: any) => {
      realtimeListener = listener;
      return () => {
        realtimeListener = null;
      };
    },
  }),
}));

vi.mock('../model/NotificationsContext', () => ({
  useNotificationsState: () => notificationsState,
}));

vi.mock('notistack', () => ({
  useSnackbar: () => ({
    enqueueSnackbar: enqueueSnackbarMock,
    closeSnackbar: closeSnackbarMock,
  }),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => navigateMock,
    useLocation: () => ({
      pathname: currentPathname,
      search: '',
      hash: '',
      key: 'test',
      state: null,
    }),
  };
});

const messageNotification = (id: number, offerId: number): Notification => ({
  id,
  type: 'message.created',
  severity: 'info',
  title: `Message #${id}`,
  body: 'New chat message',
  entity_type: 'message',
  entity_id: id,
  link_url: `/offers/${offerId}/workspace`,
  payload: { offer_id: offerId, chat_id: offerId, message_id: id },
  read_at: null,
  created_at: `2026-05-15T10:00:0${id}Z`,
});

const emitRealtimeNotificationCreated = (notification: Notification) => {
  realtimeListener?.({
    type: 'notification.created',
    event_id: 'event-1',
    ts: '2026-05-15T10:00:00Z',
    data: {
      notification,
      has_unread: true,
    },
  });
};

describe('NotificationsPushLayer', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    enqueueSnackbarMock.mockReset();
    closeSnackbarMock.mockReset();
    navigateMock.mockReset();
    notificationsState.markOneAsRead.mockReset();
    notificationsState.markOneAsRead.mockResolvedValue(undefined);
    currentPathname = '/requests';
    isAuthenticated = true;
    realtimeListener = null;

    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation(() => ({
        matches: false,
        media: '(max-width: 600px)',
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('does not show push for message.created in currently open chat', async () => {
    currentPathname = '/offers/11/workspace';
    render(<NotificationsPushLayer />);

    act(() => {
      emitRealtimeNotificationCreated(messageNotification(1, 11));
      vi.advanceTimersByTime(700);
    });

    expect(enqueueSnackbarMock).not.toHaveBeenCalled();
  });

  it('shows push for message.created from another chat and marks as read on click', async () => {
    currentPathname = '/offers/99/workspace';
    render(<NotificationsPushLayer />);

    act(() => {
      emitRealtimeNotificationCreated(messageNotification(2, 11));
      vi.advanceTimersByTime(700);
    });

    expect(enqueueSnackbarMock).toHaveBeenCalledTimes(1);

    const enqueueOptions = enqueueSnackbarMock.mock.calls[0][1] as {
      content: () => ReactElement;
    };

    render(enqueueOptions.content());
    const pushTitle = screen.getByText('Message #2');
    const pushButton = pushTitle.closest('[role="button"]');
    expect(pushButton).toBeTruthy();
    await act(async () => {
      fireEvent.click(pushButton as HTMLElement);
      await Promise.resolve();
    });

    expect(notificationsState.markOneAsRead).toHaveBeenCalledWith(2);
    expect(navigateMock).toHaveBeenCalledWith('/offers/11/workspace');
  });

  it('does not show duplicate push for the same notification id', async () => {
    render(<NotificationsPushLayer />);

    act(() => {
      emitRealtimeNotificationCreated(messageNotification(3, 11));
      emitRealtimeNotificationCreated(messageNotification(3, 11));
      vi.advanceTimersByTime(700);
    });

    expect(enqueueSnackbarMock).toHaveBeenCalledTimes(1);
  });

  it('shows a single aggregated push for 3+ notifications in a short burst', async () => {
    render(<NotificationsPushLayer />);

    act(() => {
      emitRealtimeNotificationCreated(messageNotification(21, 11));
      emitRealtimeNotificationCreated(messageNotification(22, 11));
      emitRealtimeNotificationCreated(messageNotification(23, 12));
      vi.advanceTimersByTime(700);
    });

    expect(enqueueSnackbarMock).toHaveBeenCalledTimes(1);

    expect(enqueueSnackbarMock.mock.calls[0][0]).toContain('У вас 3 новых уведомлений');
  });
});
