import ChatBubbleOutlineRounded from '@mui/icons-material/ChatBubbleOutlineRounded';
import CheckCircleOutlineRounded from '@mui/icons-material/CheckCircleOutlineRounded';
import DescriptionOutlined from '@mui/icons-material/DescriptionOutlined';
import ErrorOutlineRounded from '@mui/icons-material/ErrorOutlineRounded';
import InfoOutlined from '@mui/icons-material/InfoOutlined';
import NotificationsActiveOutlined from '@mui/icons-material/NotificationsActiveOutlined';
import WarningAmberRounded from '@mui/icons-material/WarningAmberRounded';
import type { Theme } from '@mui/material/styles';
import type { ReactNode } from 'react';
import type { NotificationSeverity } from '../model/types';

const typeIconMap: Record<string, ReactNode> = {
  'offer.created': <DescriptionOutlined fontSize="small" />,
  'offer.files_changed': <DescriptionOutlined fontSize="small" />,
  'message.created': <ChatBubbleOutlineRounded fontSize="small" />,
  'email.sent': <CheckCircleOutlineRounded fontSize="small" />,
  'email.failed': <ErrorOutlineRounded fontSize="small" />,
  'request.files_changed': <InfoOutlined fontSize="small" />,
  'request.status_changed': <InfoOutlined fontSize="small" />,
  'user.status_changed': <InfoOutlined fontSize="small" />,
  'system.warning': <WarningAmberRounded fontSize="small" />,
};

export const getNotificationTypeIcon = (type: string): ReactNode =>
  typeIconMap[type] ?? <NotificationsActiveOutlined fontSize="small" />;

export const getNotificationSeverityColor = (theme: Theme, severity: NotificationSeverity): string => {
  if (severity === 'success') {
    return theme.palette.success.main;
  }
  if (severity === 'warning') {
    return theme.palette.warning.main;
  }
  if (severity === 'error') {
    return theme.palette.error.main;
  }
  return theme.palette.info.main;
};
