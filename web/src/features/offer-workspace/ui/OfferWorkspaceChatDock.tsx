import type { ReactNode } from 'react';
import ChatRoundedIcon from '@mui/icons-material/ChatRounded';
import { Box, Fab, Paper } from '@mui/material';
import { MOBILE_BOTTOM_NAV_OFFSET, useIsMobileViewport } from '@shared/lib/responsive';

type OfferWorkspaceChatDockProps = {
  isOpen: boolean;
  onOpen: () => void;
  children: ReactNode;
};

export const OFFER_WORKSPACE_CHAT_WIDTH_PX = 430;

export const OfferWorkspaceChatDock = ({ isOpen, onOpen, children }: OfferWorkspaceChatDockProps) => {
  const isMobileViewport = useIsMobileViewport();

  return (
    <>
      {isOpen ? (
        <Box
          sx={{
            position: 'fixed',
            top: 0,
            right: 0,
            width: { xs: '100vw', lg: OFFER_WORKSPACE_CHAT_WIDTH_PX },
            height: '100dvh',
            zIndex: (theme) => theme.zIndex.drawer + 1
          }}
        >
          <Paper
            square
            sx={{
              width: '100%',
              height: '100%',
              borderLeft: (theme) => `1px solid ${theme.palette.divider}`,
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column'
            }}
          >
            {children}
          </Paper>
        </Box>
      ) : null}

      {!isOpen ? (
        <Fab
          color="primary"
          size="medium"
          aria-label="Открыть чат"
          onClick={onOpen}
          sx={{
            position: 'fixed',
            right: 16,
            top: isMobileViewport ? 'auto' : '50%',
            bottom: isMobileViewport ? `calc(${MOBILE_BOTTOM_NAV_OFFSET} + 12px)` : 'auto',
            transform: isMobileViewport ? 'none' : 'translateY(-50%)',
            zIndex: (theme) => theme.zIndex.drawer + 1
          }}
        >
          <ChatRoundedIcon />
        </Fab>
      ) : null}
    </>
  );
};
