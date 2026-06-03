import { Box, ClickAwayListener, Portal } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import type { NotificationCenterPanelProps } from './NotificationCenterPanel';
import type { NotificationCenterAnchor } from './notificationCenterLayout';
import { NotificationCenterPanel } from './NotificationCenterPanel';
import { useNotificationCenterSize } from './useNotificationCenterSize';

type NotificationCenterDrawerProps = Omit<NotificationCenterPanelProps, 'size' | 'resizeHandleProps'> & {
  anchorCorner: NotificationCenterAnchor | null;
  open: boolean;
};

export const NotificationCenterDrawer = ({
  anchorCorner: _anchorCorner,
  open,
  ...panelProps
}: NotificationCenterDrawerProps) => {
  const theme = useTheme();
  const { size, resizeHandleProps } = useNotificationCenterSize();

  if (!open) {
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
            inset: 0,
            zIndex: theme.zIndex.modal,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            bgcolor: 'rgba(17, 24, 39, 0.36)'
          }}
        >
          <Box
            sx={{
              width: '100vw',
              height: '100vh',
              maxWidth: '100vw',
              maxHeight: '100vh',
              bgcolor: 'background.paper',
              borderRadius: 0,
              overflow: 'hidden',
              boxSizing: 'border-box'
            }}
          >
            <NotificationCenterPanel
              {...panelProps}
              size={size}
              showResizeHandle={false}
              resizeHandleProps={resizeHandleProps}
            />
          </Box>
        </Box>
      </ClickAwayListener>
    </Portal>
  );
};
