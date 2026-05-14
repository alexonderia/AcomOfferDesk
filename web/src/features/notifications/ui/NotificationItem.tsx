import ChatBubbleOutlineRounded from '@mui/icons-material/ChatBubbleOutlineRounded';
import CheckCircleOutlineRounded from '@mui/icons-material/CheckCircleOutlineRounded';
import DescriptionOutlined from '@mui/icons-material/DescriptionOutlined';
import ErrorOutlineRounded from '@mui/icons-material/ErrorOutlineRounded';
import InfoOutlined from '@mui/icons-material/InfoOutlined';
import NotificationsActiveOutlined from '@mui/icons-material/NotificationsActiveOutlined';
import WarningAmberRounded from '@mui/icons-material/WarningAmberRounded';
import {
  Box,
  Chip,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  Typography,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import { formatDate } from '@shared/lib/formatters';
import type { ReactNode } from 'react';
import type { Notification } from '../model/types';

type NotificationItemProps = {
  notification: Notification;
  disabled?: boolean;
  onClick: (notification: Notification) => void;
};

const typeIconMap: Record<string, ReactNode> = {
  'offer.created': <DescriptionOutlined fontSize="small" />,
  'message.created': <ChatBubbleOutlineRounded fontSize="small" />,
  'email.sent': <CheckCircleOutlineRounded fontSize="small" />,
  'email.failed': <ErrorOutlineRounded fontSize="small" />,
  'request.status_changed': <InfoOutlined fontSize="small" />,
  'system.warning': <WarningAmberRounded fontSize="small" />,
};

const severityColorMap: Record<Notification['severity'], 'default' | 'info' | 'success' | 'warning' | 'error'> = {
  info: 'info',
  success: 'success',
  warning: 'warning',
  error: 'error',
};

const resolveIcon = (notification: Notification) =>
  typeIconMap[notification.type] ?? <NotificationsActiveOutlined fontSize="small" />;

export const NotificationItem = ({
  notification,
  disabled = false,
  onClick,
}: NotificationItemProps) => {
  const isUnread = notification.read_at === null;

  return (
    <ListItemButton
      onClick={() => onClick(notification)}
      disabled={disabled}
      sx={(theme) => ({
        alignItems: 'flex-start',
        borderRadius: 1.5,
        border: '1px solid',
        borderColor: isUnread ? alpha(theme.palette.primary.main, 0.32) : 'divider',
        backgroundColor: isUnread ? alpha(theme.palette.primary.main, 0.06) : 'transparent',
        py: 1.1,
        px: 1.25,
        '& + &': {
          mt: 1,
        },
      })}
    >
      <ListItemIcon sx={{ minWidth: 34, mt: 0.2 }}>{resolveIcon(notification)}</ListItemIcon>
      <ListItemText
        primary={
          <Stack direction="row" alignItems="center" spacing={1} sx={{ minWidth: 0 }}>
            <Typography variant="body2" sx={{ fontWeight: isUnread ? 700 : 600 }}>
              {notification.title}
            </Typography>
            {isUnread ? (
              <Box
                component="span"
                sx={(theme) => ({
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  backgroundColor: theme.palette.primary.main,
                  flexShrink: 0,
                })}
              />
            ) : null}
          </Stack>
        }
        secondary={
          <Stack spacing={0.8} sx={{ mt: 0.4 }}>
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden',
              }}
            >
              {notification.body}
            </Typography>
            <Stack direction="row" spacing={1} alignItems="center">
              <Chip
                size="small"
                label={notification.severity}
                color={severityColorMap[notification.severity]}
                variant="outlined"
              />
              <Typography variant="caption" color="text.secondary">
                {formatDate(notification.created_at, true)}
              </Typography>
            </Stack>
          </Stack>
        }
      />
    </ListItemButton>
  );
};

