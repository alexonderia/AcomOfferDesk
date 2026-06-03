import CloseRounded from '@mui/icons-material/CloseRounded';
import { Box, IconButton, Stack, Typography } from '@mui/material';
import { alpha } from '@mui/material/styles';
import { formatDate } from '@shared/lib/formatters';
import type { Notification } from '../model/types';
import { NOTIFICATION_CENTER_CARD_BORDER_RADIUS_PX } from './notificationCenterLayout';
import { getNotificationSeverityColor, getNotificationTypeIcon } from './notificationVisuals';

type NotificationCardProps = {
  notification: Pick<Notification, 'type' | 'severity' | 'title' | 'body' | 'created_at'>;
  variant: 'center' | 'toast';
  isUnread?: boolean;
  disabled?: boolean;
  compact?: boolean;
  onClick?: () => void;
  onClose?: () => void;
};

export const NotificationCard = ({
  notification,
  variant,
  isUnread = false,
  disabled = false,
  compact = true,
  onClick,
  onClose,
}: NotificationCardProps) => {
  const hasCloseButton = variant === 'toast' && Boolean(onClose);

  return (
    <Stack
      direction="row"
      spacing={1}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onClick={onClick}
      onKeyDown={
        onClick
          ? (event) => {
              if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                onClick();
              }
            }
          : undefined
      }
      sx={(theme) => {
        const severityColor = getNotificationSeverityColor(theme, notification.severity);

        return {
          position: 'relative',
          width: variant === 'toast' ? { xs: 'calc(100vw - 32px)', sm: 344 } : '100%',
          maxWidth: variant === 'toast' ? { xs: 'calc(100vw - 32px)', sm: 372 } : '100%',
          minHeight: compact ? 74 : 84,
          py: compact ? 1 : 1.15,
          pl: 1.1,
          pr: hasCloseButton ? 0.55 : 1.1,
          borderRadius:
            variant === 'center' ? `${NOTIFICATION_CENTER_CARD_BORDER_RADIUS_PX}px` : 2,
          border: '1px solid',
          borderColor: alpha(severityColor, 0.24),
          bgcolor: alpha(theme.palette.background.paper, 0.96),
          boxShadow:
            variant === 'center'
              ? '0 1px 3px rgba(16, 24, 40, 0.06)'
              : 'none',
          alignItems: 'flex-start',
          cursor: onClick ? 'pointer' : 'default',
          opacity: disabled ? 0.55 : 1,
          outline: 'none',
          transition: 'background-color 0.16s ease, transform 0.16s ease',
          '&:hover': onClick
            ? {
                bgcolor: alpha(theme.palette.primary.main, 0.06),
              }
            : undefined,
        };
      }}
    >
      {isUnread ? (
        <Box
          sx={(theme) => ({
            position: 'absolute',
            left: 8,
            top: 10,
            width: 6,
            height: 6,
            borderRadius: '50%',
            bgcolor: theme.palette.primary.main,
          })}
        />
      ) : null}

      <Box
        sx={(theme) => ({
          mt: 0.2,
          width: 28,
          height: 28,
          borderRadius: '50%',
          display: 'grid',
          placeItems: 'center',
          color: getNotificationSeverityColor(theme, notification.severity),
          bgcolor: alpha(getNotificationSeverityColor(theme, notification.severity), 0.12),
          flexShrink: 0,
        })}
      >
        {getNotificationTypeIcon(notification.type)}
      </Box>

      <Stack spacing={0.35} sx={{ minWidth: 0, flex: 1 }}>
        <Typography
          sx={{
            fontSize: 13.4,
            lineHeight: 1.25,
            fontWeight: isUnread ? 600 : 500,
          }}
        >
          {notification.title}
        </Typography>
        <Typography
          color="text.secondary"
          sx={{
            fontSize: 12.2,
            lineHeight: 1.28,
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
          }}
        >
          {notification.body}
        </Typography>
        <Typography color="text.secondary" sx={{ fontSize: 11.2, lineHeight: 1.2 }}>
          {formatDate(notification.created_at, true)}
        </Typography>
      </Stack>

      {hasCloseButton ? (
        <IconButton
          size="small"
          aria-label="Close notification"
          onClick={(event) => {
            event.stopPropagation();
            onClose?.();
          }}
          sx={{ mt: -0.2, mr: -0.15 }}
        >
          <CloseRounded sx={{ fontSize: 16 }} />
        </IconButton>
      ) : null}
    </Stack>
  );
};
