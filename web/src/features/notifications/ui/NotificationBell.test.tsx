import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { ThemeProvider } from '@mui/material';
import { appTheme } from '@shared/theme/appTheme';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { Notification } from '../model/types';
import { NotificationBell } from './NotificationBell';

const loadNotificationsMock = vi.fn();
const markOneAsReadMock = vi.fn();
const markAllAsReadMock = vi.fn();
const navigateMock = vi.fn();
const enqueueSnackbarMock = vi.fn();

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
  unreadCount: 3,
  isLoadingList: false,
  listError: null as string | null,
  isMarkAllPending: false,
  markingIds: new Set<number>(),
  loadNotifications: loadNotificationsMock,
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

vi.mock('notistack', () => ({
  useSnackbar: () => ({
    enqueueSnackbar: enqueueSnackbarMock,
  }),
}));

vi.mock('../model/NotificationsContext', () => ({
  useNotificationsState: () => notificationsState,
}));

describe('NotificationBell', () => {
  beforeEach(() => {
    loadNotificationsMock.mockReset();
    markOneAsReadMock.mockReset();
    markAllAsReadMock.mockReset();
    navigateMock.mockReset();
    enqueueSnackbarMock.mockReset();

    notificationsState.items = [];
    notificationsState.unreadCount = 3;
    notificationsState.listError = null;
    notificationsState.isLoadingList = false;
    notificationsState.isMarkAllPending = false;
    notificationsState.markingIds = new Set<number>();
  });

  it('shows unread badge and loads notifications on click', async () => {
    loadNotificationsMock.mockResolvedValue(undefined);

    render(
      <ThemeProvider theme={appTheme}>
        <NotificationBell />
      </ThemeProvider>
    );

    expect(screen.getByText('3')).toBeInTheDocument();

    fireEvent.click(screen.getAllByRole('button')[0]);

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
        <NotificationBell />
      </ThemeProvider>
    );

    fireEvent.click(screen.getAllByRole('button')[0]);

    const notificationTitle = await screen.findByText('New message');
    const clickableNotification = notificationTitle.closest('[role="button"]');
    expect(clickableNotification).toBeTruthy();
    fireEvent.click(clickableNotification as HTMLElement);

    await waitFor(() => {
      expect(markOneAsReadMock).toHaveBeenCalledWith(11);
    });
    expect(navigateMock).toHaveBeenCalledWith('/offers/11/workspace');
  });
});
