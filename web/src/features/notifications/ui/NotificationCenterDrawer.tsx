import CloseRounded from '@mui/icons-material/CloseRounded';
import { Alert, Box, CircularProgress, Drawer, IconButton, List, Stack, Typography } from '@mui/material';
import { ActionButton } from '@shared/components/ActionButton';
import type { ReactNode } from 'react';
import type { Notification } from '../model/types';
import { NotificationEmptyState } from './NotificationEmptyState';
import { NotificationItem } from './NotificationItem';

type NotificationCenterDrawerProps = {
  open: boolean;
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
};

export const NotificationCenterDrawer = ({
  open,
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
}: NotificationCenterDrawerProps) => (
  <Drawer
    anchor="right"
    open={open}
    onClose={onClose}
    PaperProps={{
      sx: {
        width: 'min(420px, 100vw)',
        p: 1.25,
      },
    }}
  >
    <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ px: 0.5, pb: 1 }}>
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

    {filterControls ? <Box sx={{ pb: 1 }}>{filterControls}</Box> : null}

    {isLoading ? (
      <Stack alignItems="center" justifyContent="center" sx={{ minHeight: 180 }}>
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
      <Box sx={{ overflowY: 'auto', pr: 0.5, pb: 0.5 }}>
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
  </Drawer>
);

