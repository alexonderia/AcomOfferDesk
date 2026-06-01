import { NotificationCenterPopover } from './NotificationCenterPopover';
import type { NotificationCenterPanelProps } from './NotificationCenterPanel';
import type { NotificationCenterAnchor } from './notificationCenterLayout';

type NotificationCenterDrawerProps = Omit<NotificationCenterPanelProps, 'size' | 'resizeHandleProps'> & {
  anchorCorner: NotificationCenterAnchor | null;
  open: boolean;
};

/** Mobile uses the same bottom-left anchored floating panel as desktop. */
export const NotificationCenterDrawer = (props: NotificationCenterDrawerProps) => (
  <NotificationCenterPopover {...props} />
);
