import { Stack, Typography } from '@mui/material';
import { alpha, useTheme } from '@mui/material/styles';
import type { ReactNode } from 'react';

export type StatusPillTone = 'success' | 'warning' | 'error' | 'info' | 'neutral';

type StatusPillProps = {
  label: string;
  tone: StatusPillTone;
  icon?: ReactNode;
  iconOnly?: boolean;
};

export const StatusPill = ({ label, tone, icon, iconOnly = false }: StatusPillProps) => {
  const theme = useTheme();
  const color =
    tone === 'success'
      ? theme.palette.success.main
      : tone === 'warning'
      ? theme.palette.warning.main
      : tone === 'error'
      ? theme.palette.error.main
      : tone === 'info'
      ? theme.palette.info.main
      : theme.palette.text.secondary;

  return (
    <Stack
      component="span"
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        maxWidth: '100%',
        px: iconOnly ? 0.55 : 1.2,
        minHeight: 28,
        minWidth: iconOnly ? 28 : 0,
        borderRadius: '999px',
        border: '1.5px solid',
        borderColor: color,
        bgcolor: alpha(color, 0.1),
        whiteSpace: 'nowrap',
        overflow: 'hidden',
      }}
    >
      {icon ? (
        <Stack
          component="span"
          sx={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            mr: iconOnly ? 0 : 0.5,
            color
          }}
        >
          {icon}
        </Stack>
      ) : null}
      {!iconOnly ? (
        <Typography
          component="span"
          sx={{
            minWidth: 0,
            maxWidth: '100%',
            display: 'block',
            fontSize: 13,
            fontWeight: 600,
            color,
            lineHeight: 1.15,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {label}
        </Typography>
      ) : null}
    </Stack>
  );
};
