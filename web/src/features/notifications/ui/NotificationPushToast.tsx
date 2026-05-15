import { forwardRef } from 'react';
import type { Notification } from '../model/types';
import { NotificationCard } from './NotificationCard';

type NotificationPushToastProps = {
  notification: Pick<Notification, 'type' | 'severity' | 'title' | 'body' | 'created_at'>;
  onClose: () => void;
  onClick: () => void;
};

export const NotificationPushToast = forwardRef<HTMLDivElement, NotificationPushToastProps>(
  ({ notification, onClose, onClick }, ref) => (
    <div ref={ref}>
      <NotificationCard
        notification={notification}
        variant="toast"
        isUnread
        compact
        onClose={onClose}
        onClick={onClick}
      />
    </div>
  )
);

NotificationPushToast.displayName = 'NotificationPushToast';
