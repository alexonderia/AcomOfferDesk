import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { ThemeProvider } from '@mui/material';
import { appTheme } from '@shared/theme/appTheme';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { Notification } from '../model/types';
import { NotificationBell } from './NotificationBell';

const loadNotificationsMock = vi.fn();
const loadMoreNotificationsMock = vi.fn();
const markOneAsReadMock = vi.fn();
const markAllAsReadMock = vi.fn();
const navigateMock = vi.fn();

const notificationItem: Notification = {
  id: 11,
  type: 'message.created',
  severity: 'info',
  title: 'New message',
  body: 'Body',
  entity_type: 'message',
  entity_id: 11,
  link_url: '/offers/11/workspace',
  payload: { offer_id: 11, chat_id: 11 },
  read_at: null,
  created_at: '2026-05-14T10:00:00Z',
};

const notificationsState = {
  items: [] as Notification[],
  hasUnread: true,
  isLoadingList: false,
  listError: null as string | null,
  isMarkAllPending: false,
  markingIds: new Set<number>(),
  hasMore: false,
  isLoadingMore: false,
  loadNotifications: loadNotificationsMock,
  loadMoreNotifications: loadMoreNotificationsMock,
  markOneAsRead: markOneAsReadMock,
  markAllAsRead: markAllAsReadMock,
};

vi.mock('@app/providers/AuthProvider', () => ({
  useAuth: () => ({
    isAuthenticated: true,
  }),
}));

vi.mock('@shared/lib/responsive', () => ({
  useIsMobileViewport: () => false,
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

vi.mock('../model/NotificationsContext', () => ({
  useNotificationsState: () => notificationsState,
}));

vi.mock('./NotificationCenterPopover', () => ({
  NotificationCenterPopover: ({
    notifications,
    onNotificationClick,
  }: {
    notifications: Notification[];
    // eslint-disable-next-line no-unused-vars -- callback param name in mock prop type
    onNotificationClick: (notification: Notification) => void;
  }) => (
    <div data-testid="notification-popover">
      {notifications.map((notification) => (
        <button
          key={notification.id}
          type="button"
          onClick={() => onNotificationClick(notification)}
        >
          {notification.title}
        </button>
      ))}
    </div>
  ),
}));

vi.mock('./NotificationCenterDrawer', () => ({
  NotificationCenterDrawer: () => null,
}));

describe('NotificationBell', () => {
  beforeEach(() => {
    loadNotificationsMock.mockReset();
    loadMoreNotificationsMock.mockReset();
    markOneAsReadMock.mockReset();
    markAllAsReadMock.mockReset();
    navigateMock.mockReset();

    notificationsState.items = [];
    notificationsState.hasUnread = true;
    notificationsState.listError = null;
    notificationsState.isLoadingList = false;
    notificationsState.isMarkAllPending = false;
    notificationsState.markingIds = new Set<number>();
  });

  it('shows unread dot (without numeric count) and loads notifications on click', async () => {
    loadNotificationsMock.mockResolvedValue(undefined);

    const { container } = render(
      <ThemeProvider theme={appTheme}>
        <NotificationBell variant="floating" />
      </ThemeProvider>
    );

    expect(screen.queryByText('3')).not.toBeInTheDocument();
    expect(container.querySelector('.MuiBadge-badge')).toBeTruthy();

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Открыть уведомления/i }));
    });

    await waitFor(() => {
      expect(loadNotificationsMock).toHaveBeenCalledTimes(1);
    });
  });

  it('marks notification as read and navigates on notification click', async () => {
    loadNotificationsMock.mockResolvedValue(undefined);
    markOneAsReadMock.mockResolvedValue(undefined);
    notificationsState.items = [notificationItem];

    render(
      <ThemeProvider theme={appTheme}>
        <NotificationBell variant="floating" />
      </ThemeProvider>
    );

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Открыть уведомления/i }));
    });

    const notificationTitle = await screen.findByText('New message');
    const clickableNotification = notificationTitle.closest('button');
    expect(clickableNotification).toBeTruthy();
    fireEvent.click(clickableNotification as HTMLButtonElement);

    await waitFor(() => {
      expect(markOneAsReadMock).toHaveBeenCalledWith(11);
    });
    expect(navigateMock).toHaveBeenCalledWith('/offers/11/workspace');
  });

  it('expands grouped notifications without closing center or navigating', async () => {
    loadNotificationsMock.mockResolvedValue(undefined);
    notificationsState.items = [
      notificationItem,
      {
        ...notificationItem,
        id: 12,
        title: 'Another message',
        body: 'Another body',
        entity_id: 12,
        link_url: '/offers/12/workspace',
        payload: { offer_id: 12, chat_id: 12 },
      },
    ];

    render(
      <ThemeProvider theme={appTheme}>
        <NotificationBell variant="floating" />
      </ThemeProvider>
    );

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Открыть уведомления/i }));
    });

    const groupedTitle = await screen.findByText('Новые сообщения (2)');
    fireEvent.click(groupedTitle.closest('button') as HTMLButtonElement);

    expect(screen.getByText('New message')).toBeInTheDocument();
    expect(screen.getByText('Another message')).toBeInTheDocument();
    expect(markOneAsReadMock).not.toHaveBeenCalled();
    expect(navigateMock).not.toHaveBeenCalled();
    expect(screen.getByTestId('notification-popover')).toBeInTheDocument();
  });
});
