import ChatBubbleOutlineRounded from '@mui/icons-material/ChatBubbleOutlineRounded';
import CheckCircleOutlineRounded from '@mui/icons-material/CheckCircleOutlineRounded';
import DescriptionOutlined from '@mui/icons-material/DescriptionOutlined';
import ErrorOutlineRounded from '@mui/icons-material/ErrorOutlineRounded';
import InfoOutlined from '@mui/icons-material/InfoOutlined';
import NotificationsActiveOutlined from '@mui/icons-material/NotificationsActiveOutlined';
import WarningAmberRounded from '@mui/icons-material/WarningAmberRounded';
import { Box, IconButton, Stack, Typography } from '@mui/material';
import CloseRounded from '@mui/icons-material/CloseRounded';
import { alpha } from '@mui/material/styles';
import { forwardRef } from 'react';
import type { ReactNode } from 'react';
import type { Notification } from '../model/types';

type NotificationPushToastProps = {
  notification: Notification;
  onClose: () => void;
  onClick: () => void;
};

const iconByType: Record<string, ReactNode> = {
  'offer.created': <DescriptionOutlined fontSize="small" />,
  'message.created': <ChatBubbleOutlineRounded fontSize="small" />,
  'email.sent': <CheckCircleOutlineRounded fontSize="small" />,
  'email.failed': <ErrorOutlineRounded fontSize="small" />,
  'request.status_changed': <InfoOutlined fontSize="small" />,
  'system.warning': <WarningAmberRounded fontSize="small" />,
};

const borderBySeverity: Record<Notification['severity'], string> = {
  info: '#1976d2',
  success: '#2e7d32',
  warning: '#ed6c02',
  error: '#d32f2f',
};

export const NotificationPushToast = forwardRef<HTMLDivElement, NotificationPushToastProps>(
  ({ notification, onClose, onClick }, ref) => {
    const icon = iconByType[notification.type] ?? <NotificationsActiveOutlined fontSize="small" />;

    return (
      <Stack
        ref={ref}
        role="button"
        tabIndex={0}
        onClick={onClick}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            onClick();
          }
        }}
        direction="row"
        spacing={1}
        sx={(theme) => ({
          width: 268,
          maxWidth: 'calc(100vw - 16px)',
          py: 0.55,
          pl: 0.85,
          pr: 0.4,
          borderRadius: 1.2,
          border: '1px solid',
          borderColor: alpha(borderBySeverity[notification.severity], 0.45),
          bgcolor: 'background.paper',
          boxShadow: '0 6px 14px rgba(0,0,0,0.14)',
          alignItems: 'flex-start',
          cursor: 'pointer',
          outline: 'none',
          '&:hover': {
            bgcolor: alpha(theme.palette.primary.main, 0.05),
          },
        })}
      >
        <Box sx={{ mt: 0.16, lineHeight: 1 }}>{icon}</Box>
        <Stack spacing={0.15} sx={{ minWidth: 0, flex: 1 }}>
          <Typography variant="caption" sx={{ fontWeight: 700, lineHeight: 1.2, fontSize: 12 }}>
            {notification.title}
          </Typography>
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{
              lineHeight: 1.22,
              fontSize: 11.5,
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}
          >
            {notification.body}
          </Typography>
        </Stack>
        <IconButton
          size="small"
          aria-label="Закрыть"
          onClick={(event) => {
            event.stopPropagation();
            onClose();
          }}
          sx={{ mt: -0.35 }}
        >
          <CloseRounded sx={{ fontSize: 15 }} />
        </IconButton>
      </Stack>
    );
  }
);

NotificationPushToast.displayName = 'NotificationPushToast';
