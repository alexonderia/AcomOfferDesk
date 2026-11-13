import { Box, Tooltip } from '@mui/material';

type WarningTooltipProps = {
  message?: string | null;
  severity?: 'warning' | 'error';
};

export const WarningTooltip = ({ message, severity = 'warning' }: WarningTooltipProps) => {
  if (!message) return null;
  const isError = severity === 'error';
  return (
    <Tooltip title={message} arrow>
      <Box
        component="span"
        tabIndex={0}
        role="img"
        aria-label={message}
        onClick={(event) => event.stopPropagation()}
        sx={{
          width: 18, height: 18, borderRadius: '50%',
          backgroundColor: isError ? '#fef2f2' : '#fff7ed',
          border: `1px solid ${isError ? '#ef4444' : '#f59e0b'}`,
          color: isError ? '#dc2626' : '#d97706',
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 12, fontWeight: 800, lineHeight: 1, cursor: 'help', flexShrink: 0,
        }}
      >
        !
      </Box>
    </Tooltip>
  );
};
