import { Box, ClickAwayListener, Portal } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import {
  NOTIFICATION_CENTER_PANEL_BORDER_RADIUS_PX,
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
            width: size.width,
            height: size.height,
            maxWidth: 'calc(100vw - 16px)',
            maxHeight: `min(90vh, calc(100vh - ${anchorCorner.bottom}px - 16px))`,
            minWidth: 320,
            minHeight: 360,
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
