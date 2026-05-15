import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { ReactElement } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { NotificationsPushLayer } from './NotificationsPushLayer';
import type { Notification } from '../model/types';

const enqueueSnackbarMock = vi.fn();
const closeSnackbarMock = vi.fn();
const navigateMock = vi.fn();

let currentPathname = '/requests';
let isAuthenticated = true;

const notificationsState = {
  unreadCount: 0,
  loadNotifications: vi.fn(),
  markOneAsRead: vi.fn()
};

vi.mock('../model/constants', () => ({
  NOTIFICATION_PUSH_AUTOCLOSE_MS: 10_000,
  NOTIFICATION_PUSH_ERROR_AUTOCLOSE_MS: 14_000,
  NOTIFICATION_PUSH_BURST_THRESHOLD: 3,
  NOTIFICATION_PUSH_REFRESH_THROTTLE_MS: 1,
}));

vi.mock('@app/providers/AuthProvider', () => ({
  useAuth: () => ({
    isAuthenticated,
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

describe('NotificationsPushLayer', () => {
  beforeEach(() => {
    enqueueSnackbarMock.mockReset();
    closeSnackbarMock.mockReset();
    navigateMock.mockReset();
    notificationsState.loadNotifications.mockReset();
    notificationsState.markOneAsRead.mockReset();
    notificationsState.markOneAsRead.mockResolvedValue(undefined);
    notificationsState.unreadCount = 0;
    currentPathname = '/requests';
    isAuthenticated = true;

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

  it('does not show push for message.created in currently open chat', async () => {
    currentPathname = '/offers/11/workspace';

    notificationsState.loadNotifications
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([messageNotification(1, 11)]);

    const { rerender } = render(<NotificationsPushLayer />);

    await waitFor(() => {
      expect(notificationsState.loadNotifications).toHaveBeenCalledTimes(1);
    });

    notificationsState.unreadCount = 1;
    rerender(<NotificationsPushLayer />);

    await waitFor(() => {
      expect(notificationsState.loadNotifications).toHaveBeenCalledTimes(2);
    });

    expect(enqueueSnackbarMock).not.toHaveBeenCalled();
  });

  it('shows push for message.created from another chat and marks as read on click', async () => {
    currentPathname = '/offers/99/workspace';

    notificationsState.loadNotifications
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([messageNotification(2, 11)]);

    const { rerender } = render(<NotificationsPushLayer />);

    await waitFor(() => {
      expect(notificationsState.loadNotifications).toHaveBeenCalledTimes(1);
    });

    notificationsState.unreadCount = 1;
    rerender(<NotificationsPushLayer />);

    await waitFor(() => {
      expect(enqueueSnackbarMock).toHaveBeenCalledTimes(1);
    });

    const enqueueOptions = enqueueSnackbarMock.mock.calls[0][1] as {
      content: () => ReactElement;
    };

    render(enqueueOptions.content());
    const pushTitle = screen.getByText('Message #2');
    const pushButton = pushTitle.closest('[role="button"]');
    expect(pushButton).toBeTruthy();
    fireEvent.click(pushButton as HTMLElement);

    await waitFor(() => {
      expect(notificationsState.markOneAsRead).toHaveBeenCalledWith(2);
    });
    expect(navigateMock).toHaveBeenCalledWith('/offers/11/workspace');
  });

  it('does not show duplicate push for the same notification id', async () => {
    notificationsState.loadNotifications
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([messageNotification(3, 11)])
      .mockResolvedValueOnce([messageNotification(3, 11)]);

    const { rerender } = render(<NotificationsPushLayer />);

    await waitFor(() => {
      expect(notificationsState.loadNotifications).toHaveBeenCalledTimes(1);
    });

    notificationsState.unreadCount = 1;
    rerender(<NotificationsPushLayer />);

    await waitFor(() => {
      expect(enqueueSnackbarMock).toHaveBeenCalledTimes(1);
    });

    notificationsState.unreadCount = 2;
    rerender(<NotificationsPushLayer />);

    await waitFor(() => {
      expect(notificationsState.loadNotifications).toHaveBeenCalledTimes(3);
    });

    expect(enqueueSnackbarMock).toHaveBeenCalledTimes(1);
  });

  it('does not run parallel loadNotifications during unread spikes', async () => {
    vi.useFakeTimers();

    let loadCalls = 0;
    let inFlight = 0;
    let maxInFlight = 0;

    notificationsState.loadNotifications.mockImplementation(() => {
      loadCalls += 1;
      if (loadCalls === 1) {
        return Promise.resolve([]);
      }

      inFlight += 1;
      maxInFlight = Math.max(maxInFlight, inFlight);
      return new Promise((resolve) => {
        window.setTimeout(() => {
          inFlight -= 1;
          resolve([messageNotification(10 + loadCalls, 13)]);
        }, 25);
      });
    });

    const { rerender } = render(<NotificationsPushLayer />);

    await act(async () => {
      await Promise.resolve();
    });

    notificationsState.unreadCount = 1;
    rerender(<NotificationsPushLayer />);

    notificationsState.unreadCount = 2;
    rerender(<NotificationsPushLayer />);

    await act(async () => {
      vi.advanceTimersByTime(60);
      await Promise.resolve();
    });

    expect(maxInFlight).toBe(1);

    vi.useRealTimers();
  });

  it('shows a single aggregated push for 3+ fresh notifications', async () => {
    notificationsState.loadNotifications
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([
        messageNotification(21, 11),
        messageNotification(22, 11),
        messageNotification(23, 12),
      ]);

    const { rerender } = render(<NotificationsPushLayer />);

    await waitFor(() => {
      expect(notificationsState.loadNotifications).toHaveBeenCalledTimes(1);
    });

    notificationsState.unreadCount = 3;
    rerender(<NotificationsPushLayer />);

    await waitFor(() => {
      expect(enqueueSnackbarMock).toHaveBeenCalledTimes(1);
    });

    expect(enqueueSnackbarMock.mock.calls[0][0]).toContain('У вас 3 новых уведомлений');
  });
});
