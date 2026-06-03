import CloseRounded from '@mui/icons-material/CloseRounded';
import { Alert, Box, CircularProgress, IconButton, List, Stack, Typography } from '@mui/material';
import { alpha } from '@mui/material/styles';
import { ActionButton } from '@shared/components/ActionButton';
import type { MouseEvent, PointerEvent, ReactNode } from 'react';
import type { Notification } from '../model/types';
import { NotificationEmptyState } from './NotificationEmptyState';
import { NotificationItem } from './NotificationItem';
import type { NotificationCenterSize } from './notificationCenterLayout';

export type NotificationCenterPanelProps = {
  notifications: Notification[];
  hasUnread: boolean;
  isLoading: boolean;
  isMarkAllPending: boolean;
  error: string | null;
  markingIds: Set<number>;
  onClose: () => void;
  onRetry: () => void;
  onMarkAll: () => void;
  filterControls?: ReactNode;
  onNotificationClick: (notification: Notification) => void;
  canLoadMore?: boolean;
  isLoadingMore?: boolean;
  onLoadMore?: () => void;
  size: NotificationCenterSize;
  showResizeHandle?: boolean;
  resizeHandleProps: {
    onPointerDown: (event: PointerEvent<HTMLElement>) => void;
    onPointerMove: (event: PointerEvent<HTMLElement>) => void;
    onPointerUp: (event: PointerEvent<HTMLElement>) => void;
    onPointerCancel: (event: PointerEvent<HTMLElement>) => void;
    onDoubleClick: (event: MouseEvent<HTMLElement>) => void;
  };
};

export const NotificationCenterPanel = ({
  notifications,
  hasUnread,
  isLoading,
  isMarkAllPending,
  error,
  markingIds,
  onClose,
  onRetry,
  onMarkAll,
  filterControls,
  onNotificationClick,
  canLoadMore = false,
  isLoadingMore = false,
  onLoadMore,
  size: _size,
  showResizeHandle = true,
  resizeHandleProps,
}: NotificationCenterPanelProps) => {
  return (
    <Box
      sx={{
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
        height: '100%',
        minWidth: 0,
        minHeight: 0,
        maxWidth: '100%',
        maxHeight: '100%',
        p: 1.25,
        boxSizing: 'border-box',
      }}
    >
      <Stack
        direction="row"
        alignItems="center"
        justifyContent="space-between"
        sx={{ px: 0.5, pb: 1, pr: 3.5, flexShrink: 0 }}
      >
        <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
          Уведомления
        </Typography>
        <Stack direction="row" alignItems="center" spacing={0.8}>
          <ActionButton
            kind="custom"
            showNavigationIcons={false}
            disabled={!hasUnread || isMarkAllPending}
            onClick={onMarkAll}
            sx={{ minHeight: 32, px: 1.4, fontSize: 13, textTransform: 'none' }}
          >
            Прочитать все
          </ActionButton>
          <IconButton size="small" onClick={onClose} aria-label="Закрыть уведомления">
            <CloseRounded fontSize="small" />
          </IconButton>
        </Stack>
      </Stack>

      {filterControls ? <Box sx={{ pb: 1, flexShrink: 0 }}>{filterControls}</Box> : null}

      <Box sx={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
        {isLoading ? (
          <Stack alignItems="center" justifyContent="center" sx={{ flex: 1, minHeight: 180 }}>
            <CircularProgress size={24} />
          </Stack>
        ) : error ? (
          <Stack spacing={1} sx={{ px: 0.5, pb: 0.5 }}>
            <Alert severity="error">{error}</Alert>
            <ActionButton
              kind="outlined"
              showNavigationIcons={false}
              onClick={onRetry}
              sx={{ minHeight: 36, textTransform: 'none' }}
            >
              Повторить
            </ActionButton>
          </Stack>
        ) : notifications.length === 0 ? (
          <NotificationEmptyState />
        ) : (
          <Box sx={{ flex: 1, minHeight: 0, overflowY: 'auto', pr: 0.5, pb: 0.5 }}>
            <List disablePadding>
              {notifications.map((notification) => (
                <NotificationItem
                  key={notification.id}
                  notification={notification}
                  disabled={markingIds.has(notification.id)}
                  onClick={onNotificationClick}
                />
              ))}
            </List>
            {canLoadMore ? (
              <Stack alignItems="center" sx={{ pt: 1.1 }}>
                <ActionButton
                  kind="outlined"
                  showNavigationIcons={false}
                  disabled={isLoadingMore}
                  onClick={onLoadMore}
                  sx={{ minHeight: 34, textTransform: 'none' }}
                >
                  {isLoadingMore ? 'Загрузка...' : 'Показать еще'}
                </ActionButton>
              </Stack>
            ) : null}
          </Box>
        )}
      </Box>

      {showResizeHandle ? (
        <Box
          role="separator"
          aria-label="Изменить размер окна уведомлений. Двойной щелчок — стандартный размер."
          {...resizeHandleProps}
          sx={(theme) => ({
            position: 'absolute',
            right: 4,
            top: 4,
            zIndex: 2,
            width: 18,
            height: 18,
            cursor: 'nesw-resize',
            touchAction: 'none',
            borderRadius: 0.5,
            '&::before': {
              content: '""',
              position: 'absolute',
              right: 3,
              top: 3,
              width: 10,
              height: 10,
              borderRight: `2px solid ${alpha(theme.palette.text.secondary, 0.55)}`,
              borderTop: `2px solid ${alpha(theme.palette.text.secondary, 0.55)}`,
            },
            '&:hover::before': {
              borderColor: theme.palette.primary.main,
            },
          })}
        />
      ) : null}
    </Box>
  );
};
