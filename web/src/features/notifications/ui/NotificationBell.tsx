import NotificationsNoneOutlined from '@mui/icons-material/NotificationsNoneOutlined';
import { Badge, Box, IconButton, Stack, Tooltip, Typography } from '@mui/material';
import { alpha, useTheme } from '@mui/material/styles';
import { useAuth } from '@app/providers/AuthProvider';
import { useIsMobileViewport } from '@shared/lib/responsive';
import { ActionButton } from '@shared/components/ActionButton';
import type { MouseEvent } from 'react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSnackbar } from 'notistack';
import { useNotificationsState } from '../model/NotificationsContext';
import { resolveNotificationLink } from '../model/resolveNotificationLink';
import type { Notification } from '../model/types';
import { NotificationCenterDrawer } from './NotificationCenterDrawer';
import { NotificationCenterPopover } from './NotificationCenterPopover';

type NotificationBellProps = {
  collapsed?: boolean;
  variant?: 'sidebar' | 'floating';
};

export const NotificationBell = ({
  collapsed = false,
  variant = 'sidebar',
}: NotificationBellProps) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const { isAuthenticated } = useAuth();
  const isMobileViewport = useIsMobileViewport();
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const {
    items,
    unreadCount,
    isLoadingList,
    listError,
    isMarkAllPending,
    markingIds,
    loadNotifications,
    markOneAsRead,
    markAllAsRead,
  } = useNotificationsState();

  if (!isAuthenticated) {
    return null;
  }

  const open = isMobileViewport ? isDrawerOpen : Boolean(anchorEl);

  const closeCenter = () => {
    setAnchorEl(null);
    setIsDrawerOpen(false);
  };

  const openCenter = async (event: MouseEvent<HTMLElement>) => {
    if (isMobileViewport) {
      setIsDrawerOpen(true);
    } else {
      setAnchorEl(event.currentTarget);
    }

    try {
      await loadNotifications();
    } catch {
      enqueueSnackbar('Не удалось загрузить уведомления', { variant: 'error' });
    }
  };

  const handleNotificationClick = async (notification: Notification) => {
    try {
      if (notification.read_at === null) {
        await markOneAsRead(notification.id);
      }
    } catch {
      enqueueSnackbar('Не удалось отметить уведомление как прочитанное', { variant: 'error' });
      return;
    }

    const routePath = resolveNotificationLink(notification.link_url);
    if (routePath) {
      closeCenter();
      navigate(routePath);
    }
  };

  const handleMarkAll = async () => {
    try {
      const updatedCount = await markAllAsRead();
      if (updatedCount > 0) {
        enqueueSnackbar('Все уведомления отмечены как прочитанные', { variant: 'success' });
      }
    } catch {
      enqueueSnackbar('Не удалось отметить уведомления как прочитанные', { variant: 'error' });
    }
  };

  const handleRetry = async () => {
    try {
      await loadNotifications();
    } catch {
      enqueueSnackbar('Не удалось загрузить уведомления', { variant: 'error' });
    }
  };

  const icon = (
    <Badge badgeContent={unreadCount} color="error" max={99}>
      <NotificationsNoneOutlined fontSize="small" />
    </Badge>
  );

  return (
    <>
      {variant === 'floating' ? (
        <Tooltip title="Уведомления" placement="top">
          <IconButton
            onClick={openCenter}
            aria-label="Открыть уведомления"
            sx={{
              border: '1px solid',
              borderColor: 'divider',
              backgroundColor: 'background.paper',
              boxShadow: 2,
              '&:hover': {
                backgroundColor: alpha(theme.palette.primary.main, 0.08),
              },
            }}
          >
            {icon}
          </IconButton>
        </Tooltip>
      ) : (
        <Tooltip title="Уведомления" placement="right" enterDelay={150} disableHoverListener={!collapsed}>
          <Stack component="span" sx={{ display: 'block', width: '100%' }}>
            <ActionButton
              kind="custom"
              showNavigationIcons={false}
              onClick={openCenter}
              sx={{
                width: '100%',
                minHeight: 42,
                minWidth: 0,
                borderRadius: `${theme.acomShape.buttonRadius}px !important`,
                justifyContent: collapsed ? 'center' : 'flex-start',
                px: collapsed ? 0 : 1.75,
                gap: collapsed ? 0 : 1.25,
                transition:
                  'background-color 0.28s ease, border-color 0.28s ease, color 0.28s ease, padding 0.32s ease, gap 0.32s ease',
              }}
            >
              <Box component="span" sx={{ display: 'inline-flex', lineHeight: 1 }}>
                {icon}
              </Box>
              <Typography
                sx={{
                  maxWidth: collapsed ? 0 : 160,
                  opacity: collapsed ? 0 : 1,
                  transform: collapsed ? 'translateX(-4px)' : 'translateX(0)',
                  overflow: 'hidden',
                  textOverflow: 'clip',
                  whiteSpace: 'nowrap',
                  fontSize: 14,
                  fontWeight: 500,
                  lineHeight: 1.2,
                  transition: 'max-width 0.34s ease, opacity 0.24s ease, transform 0.34s ease',
                }}
              >
                Уведомления
              </Typography>
            </ActionButton>
          </Stack>
        </Tooltip>
      )}

      {isMobileViewport ? (
        <NotificationCenterDrawer
          open={open}
          notifications={items}
          unreadCount={unreadCount}
          isLoading={isLoadingList}
          isMarkAllPending={isMarkAllPending}
          error={listError}
          markingIds={markingIds}
          onClose={closeCenter}
          onRetry={handleRetry}
          onMarkAll={handleMarkAll}
          onNotificationClick={handleNotificationClick}
        />
      ) : (
        <NotificationCenterPopover
          anchorEl={anchorEl}
          open={open}
          notifications={items}
          unreadCount={unreadCount}
          isLoading={isLoadingList}
          isMarkAllPending={isMarkAllPending}
          error={listError}
          markingIds={markingIds}
          onClose={closeCenter}
          onRetry={handleRetry}
          onMarkAll={handleMarkAll}
          onNotificationClick={handleNotificationClick}
        />
      )}
    </>
  );
};
