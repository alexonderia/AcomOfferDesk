import { Box, ClickAwayListener, Portal } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import {
  NOTIFICATION_CENTER_MIN_SIZE,
  NOTIFICATION_CENTER_PANEL_BORDER_RADIUS_PX,
  NOTIFICATION_CENTER_VIEWPORT_BOTTOM_INSET,
  type NotificationCenterAnchor,
} from './notificationCenterLayout';
import { NotificationCenterPanel, type NotificationCenterPanelProps } from './NotificationCenterPanel';
import { useNotificationCenterSize } from './useNotificationCenterSize';

type NotificationCenterPopoverProps = Omit<NotificationCenterPanelProps, 'size' | 'resizeHandleProps'> & {
  anchorCorner: NotificationCenterAnchor | null;
  open: boolean;
};

export const NotificationCenterPopover = ({
  anchorCorner,
  open,
  ...panelProps
}: NotificationCenterPopoverProps) => {
  const theme = useTheme();
  const { size, resizeHandleProps } = useNotificationCenterSize();

  if (!open || anchorCorner === null) {
    return null;
  }

  const viewportWidthLimit = `calc(100vw - ${anchorCorner.left}px - ${NOTIFICATION_CENTER_VIEWPORT_BOTTOM_INSET}px)`;
  const viewportHeightLimit = `calc(100vh - ${anchorCorner.bottom}px - ${NOTIFICATION_CENTER_VIEWPORT_BOTTOM_INSET}px)`;
  const minWidthLimit = `min(${NOTIFICATION_CENTER_MIN_SIZE.width}px, ${viewportWidthLimit})`;
  const minHeightLimit = `min(${NOTIFICATION_CENTER_MIN_SIZE.height}px, ${viewportHeightLimit})`;

  return (
    <Portal>
      <ClickAwayListener onClickAway={panelProps.onClose} mouseEvent="onPointerDown" touchEvent="onTouchStart">
        <Box
          role="dialog"
          aria-label="Уведомления"
          sx={{
            position: 'fixed',
            left: anchorCorner.left,
            bottom: anchorCorner.bottom,
            width: `min(${size.width}px, ${viewportWidthLimit})`,
            height: `min(${size.height}px, ${viewportHeightLimit})`,
            maxWidth: viewportWidthLimit,
            maxHeight: viewportHeightLimit,
            minWidth: minWidthLimit,
            minHeight: minHeightLimit,
            zIndex: theme.zIndex.modal,
            bgcolor: 'background.paper',
            borderRadius: `${NOTIFICATION_CENTER_PANEL_BORDER_RADIUS_PX}px`,
            boxShadow: theme.shadows[8],
            overflow: 'hidden',
            boxSizing: 'border-box',
          }}
        >
          <NotificationCenterPanel {...panelProps} size={size} resizeHandleProps={resizeHandleProps} />
        </Box>
      </ClickAwayListener>
    </Portal>
  );
};
