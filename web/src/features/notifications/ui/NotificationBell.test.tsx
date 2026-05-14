import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { ThemeProvider } from '@mui/material';
import { appTheme } from '@shared/theme/appTheme';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { NotificationBell } from './NotificationBell';

const loadNotificationsMock = vi.fn();
const markOneAsReadMock = vi.fn();
const markAllAsReadMock = vi.fn();
const navigateMock = vi.fn();
const enqueueSnackbarMock = vi.fn();

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
  useNotificationsState: () => ({
    items: [],
    unreadCount: 3,
    isLoadingList: false,
    listError: null,
    isMarkAllPending: false,
    markingIds: new Set<number>(),
    loadNotifications: loadNotificationsMock,
    markOneAsRead: markOneAsReadMock,
    markAllAsRead: markAllAsReadMock,
  }),
}));

describe('NotificationBell', () => {
  beforeEach(() => {
    loadNotificationsMock.mockReset();
    markOneAsReadMock.mockReset();
    markAllAsReadMock.mockReset();
    navigateMock.mockReset();
    enqueueSnackbarMock.mockReset();
  });

  it('shows unread badge and loads notifications on click', async () => {
    loadNotificationsMock.mockResolvedValue(undefined);

    render(
      <ThemeProvider theme={appTheme}>
        <NotificationBell />
      </ThemeProvider>
    );

    expect(screen.getByText('Уведомления')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /уведомления/i }));

    await waitFor(() => {
      expect(loadNotificationsMock).toHaveBeenCalledTimes(1);
    });
  });
});
