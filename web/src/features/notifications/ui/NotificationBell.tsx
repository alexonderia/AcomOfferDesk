import NotificationsNoneOutlined from '@mui/icons-material/NotificationsNoneOutlined';
import { Badge, Box, IconButton, Stack, Tab, Tabs, Tooltip, Typography } from '@mui/material';
import { alpha, useTheme } from '@mui/material/styles';
import { useAuth } from '@app/providers/AuthProvider';
import { useIsMobileViewport } from '@shared/lib/responsive';
import { ActionButton } from '@shared/components/ActionButton';
import type { MouseEvent } from 'react';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useNotificationsState } from '../model/NotificationsContext';
import { resolveNotificationLink } from '../model/resolveNotificationLink';
import { NOTIFICATION_PAGE_SIZE } from '../model/constants';
import type { Notification } from '../model/types';
import { NotificationCenterDrawer } from './NotificationCenterDrawer';
import { NotificationCenterPopover } from './NotificationCenterPopover';
import { captureNotificationCenterAnchor, type NotificationCenterAnchor } from './notificationCenterLayout';

type NotificationBellProps = {
  collapsed?: boolean;
  variant?: 'sidebar' | 'floating';
};

type NotificationFilter = 'all' | 'unread' | 'messages' | 'offers' | 'errors';

const buildGroupedTypeTitle = (type: string, count: number): string => {
  if (type === 'message.created') {
    return `Новые сообщения (${count})`;
  }
  if (type === 'offer.created') {
    return `Новые КП (${count})`;
  }
  if (type === 'request.status_changed') {
    return `Обновления статуса заявок (${count})`;
  }
  return `Новые уведомления (${count})`;
};

const buildGroupedTypeBody = (type: string, count: number): string => {
  if (type === 'message.created') {
    return `У вас ${count} новых сообщений.`;
  }
  if (type === 'offer.created') {
    return `У вас ${count} новых коммерческих предложений.`;
  }
  if (type === 'request.status_changed') {
    return `У вас ${count} обновлений статуса заявок.`;
  }
  return `У вас ${count} новых уведомлений этого типа.`;
};

const buildCenterDisplayNotifications = (
  items: Notification[],
  expandedGroupTypes: ReadonlySet<string>,
) => {
  const groupedUnreadByType = new Map<string, { displayIndex: number; ids: number[] }>();
  const displayNotifications: Notification[] = [];
  const sourceIdsByDisplayId = new Map<number, number[]>();

  items.forEach((item) => {
    if (item.read_at !== null) {
      displayNotifications.push(item);
      sourceIdsByDisplayId.set(item.id, [item.id]);
      return;
    }

    const existingGroup = groupedUnreadByType.get(item.type);
    if (!existingGroup) {
      displayNotifications.push(item);
      groupedUnreadByType.set(item.type, {
        displayIndex: displayNotifications.length - 1,
        ids: [item.id],
      });
      sourceIdsByDisplayId.set(item.id, [item.id]);
      return;
    }

    existingGroup.ids.push(item.id);
  });

  groupedUnreadByType.forEach(({ displayIndex, ids }) => {
    if (ids.length <= 1) {
      return;
    }

    const base = displayNotifications[displayIndex];
    const groupedNotification: Notification = {
      ...base,
      title: buildGroupedTypeTitle(base.type, ids.length),
      body: buildGroupedTypeBody(base.type, ids.length),
    };

    displayNotifications[displayIndex] = groupedNotification;
    sourceIdsByDisplayId.set(groupedNotification.id, [...ids]);
  });

  const expandedTypesRendered = new Set<string>();
  const finalDisplayNotifications: Notification[] = [];
  const finalSourceIdsByDisplayId = new Map<number, number[]>();

  displayNotifications.forEach((notification) => {
    const sourceIds = sourceIdsByDisplayId.get(notification.id) ?? [notification.id];
    const isGroupedSummary = sourceIds.length > 1;

    if (isGroupedSummary && expandedGroupTypes.has(notification.type)) {
      if (expandedTypesRendered.has(notification.type)) {
        return;
      }
      expandedTypesRendered.add(notification.type);
      items
        .filter((item) => item.type === notification.type && item.read_at === null)
        .forEach((item) => {
          finalDisplayNotifications.push(item);
          finalSourceIdsByDisplayId.set(item.id, [item.id]);
        });
      return;
    }

    finalDisplayNotifications.push(notification);
    finalSourceIdsByDisplayId.set(notification.id, sourceIds);
  });

  return {
    displayNotifications: finalDisplayNotifications,
    sourceIdsByDisplayId: finalSourceIdsByDisplayId,
  };
};

export const NotificationBell = ({
  collapsed = false,
  variant = 'sidebar',
}: NotificationBellProps) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const isMobileViewport = useIsMobileViewport();
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  const [anchorCorner, setAnchorCorner] = useState<NotificationCenterAnchor | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [activeFilter, setActiveFilter] = useState<NotificationFilter>('all');
  const [expandedGroupTypes, setExpandedGroupTypes] = useState<Set<string>>(() => new Set());

  const {
    items,
    hasUnread,
    isLoadingList,
    listError,
    isMarkAllPending,
    markingIds,
    loadNotifications,
    loadMoreNotifications,
    markOneAsRead,
    markAllAsRead,
    hasMore,
    isLoadingMore,
  } = useNotificationsState();

  const { displayNotifications, sourceIdsByDisplayId } = useMemo(
    () => buildCenterDisplayNotifications(items, expandedGroupTypes),
    [expandedGroupTypes, items]
  );

  const filteredDisplayNotifications = useMemo(() => {
    if (activeFilter === 'all') {
      return displayNotifications;
    }
    return displayNotifications.filter((notification) => {
      if (activeFilter === 'unread') {
        return notification.read_at === null;
      }
      if (activeFilter === 'messages') {
        return notification.type === 'message.created';
      }
      if (activeFilter === 'offers') {
        return notification.type === 'offer.created';
      }
      if (activeFilter === 'errors') {
        return notification.severity === 'error' || notification.severity === 'warning';
      }
      return true;
    });
  }, [activeFilter, displayNotifications]);

  const displayMarkingIds = useMemo(() => {
    const mapped = new Set<number>();
    displayNotifications.forEach((notification) => {
      const sourceIds = sourceIdsByDisplayId.get(notification.id) ?? [notification.id];
      if (sourceIds.some((id) => markingIds.has(id))) {
        mapped.add(notification.id);
      }
    });
    return mapped;
  }, [displayNotifications, markingIds, sourceIdsByDisplayId]);

  if (!isAuthenticated) {
    return null;
  }

  const open = isMobileViewport ? isDrawerOpen : Boolean(anchorEl);

  const closeCenter = () => {
    setAnchorEl(null);
    setAnchorCorner(null);
    setIsDrawerOpen(false);
    setExpandedGroupTypes(new Set());
  };

  const openCenter = async (event: MouseEvent<HTMLElement>) => {
    setAnchorCorner(captureNotificationCenterAnchor(event.currentTarget));

    if (isMobileViewport) {
      setIsDrawerOpen(true);
    } else {
      setAnchorEl(event.currentTarget);
    }

    try {
      await loadNotifications({ offset: 0, limit: NOTIFICATION_PAGE_SIZE });
    } catch {}
  };

  const handleNotificationClick = async (notification: Notification) => {
    const sourceIds = sourceIdsByDisplayId.get(notification.id) ?? [notification.id];
    const isGroupedSummary = sourceIds.length > 1;

    if (isGroupedSummary) {
      setExpandedGroupTypes((current) => {
        const next = new Set(current);
        next.add(notification.type);
        return next;
      });
      return;
    }

    closeCenter();

    try {
      if (notification.read_at === null) {
        await Promise.all(sourceIds.map((id) => markOneAsRead(id)));
      }
    } catch {
      // Center is already closed; keep UX stable even if mark-as-read fails.
    }

    const routePath = resolveNotificationLink(notification.link_url);
    if (routePath) {
      navigate(routePath);
    }
  };

  const handleMarkAll = async () => {
    try {
      await markAllAsRead();
    } catch {}
  };

  const handleRetry = async () => {
    try {
      await loadNotifications({ offset: 0, limit: NOTIFICATION_PAGE_SIZE });
    } catch {}
  };

  const filterControls = (
    <Tabs
      value={activeFilter}
      onChange={(_event, value: NotificationFilter) => setActiveFilter(value)}
      variant="scrollable"
      scrollButtons="auto"
      allowScrollButtonsMobile
      sx={{
        minHeight: 34,
        '& .MuiTabs-indicator': {
          height: 2,
          borderRadius: 2,
        },
        '& .MuiTab-root': {
          minHeight: 34,
          px: 1.2,
          fontSize: 12,
          textTransform: 'none',
        },
      }}
    >
      <Tab value="all" label="Все" />
      <Tab value="unread" label="Непрочитанные" />
      <Tab value="messages" label="Сообщения" />
      <Tab value="offers" label="КП" />
      <Tab value="errors" label="Ошибки" />
    </Tabs>
  );

  const icon = (
    <Badge color="error" variant="dot" invisible={!hasUnread}>
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
          anchorCorner={anchorCorner}
          notifications={filteredDisplayNotifications}
          hasUnread={hasUnread}
          isLoading={isLoadingList}
          isMarkAllPending={isMarkAllPending}
          error={listError}
          markingIds={displayMarkingIds}
          onClose={closeCenter}
          onRetry={handleRetry}
          onMarkAll={handleMarkAll}
          filterControls={filterControls}
          onNotificationClick={handleNotificationClick}
          canLoadMore={hasMore}
          isLoadingMore={isLoadingMore}
          onLoadMore={() => {
            void loadMoreNotifications();
          }}
        />
      ) : (
        <NotificationCenterPopover
          anchorCorner={anchorCorner}
          open={open}
          notifications={filteredDisplayNotifications}
          hasUnread={hasUnread}
          isLoading={isLoadingList}
          isMarkAllPending={isMarkAllPending}
          error={listError}
          markingIds={displayMarkingIds}
          onClose={closeCenter}
          onRetry={handleRetry}
          onMarkAll={handleMarkAll}
          filterControls={filterControls}
          onNotificationClick={handleNotificationClick}
          canLoadMore={hasMore}
          isLoadingMore={isLoadingMore}
          onLoadMore={() => {
            void loadMoreNotifications();
          }}
        />
      )}
    </>
  );
};
