import { ListItemButton } from '@mui/material';
import type { Notification } from '../model/types';
import { NotificationCard } from './NotificationCard';

type NotificationItemProps = {
  notification: Notification;
  disabled?: boolean;
  onClick: (notification: Notification) => void;
};

export const NotificationItem = ({
  notification,
  disabled = false,
  onClick,
}: NotificationItemProps) => {
  const isUnread = notification.read_at === null;

  return (
    <ListItemButton
      disableGutters
      disableRipple={disabled}
      onClick={() => onClick(notification)}
      disabled={disabled}
      sx={{
        display: 'block',
        p: 0,
        borderRadius: 2,
        '& + &': {
          mt: 0.9,
        },
      }}
    >
      <NotificationCard
        notification={notification}
        variant="center"
        isUnread={isUnread}
        compact
        disabled={disabled}
      />
    </ListItemButton>
  );
};
