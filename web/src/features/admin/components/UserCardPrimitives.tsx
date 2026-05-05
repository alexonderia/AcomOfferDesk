import { Box, Stack, Typography } from '@mui/material';
import { alpha, type Theme } from '@mui/material/styles';
import type { ReactNode } from 'react';
import { StatusPill, type StatusPillTone } from '@shared/ui/StatusPill';

const userStatusLabelByValue: Record<string, string> = {
  review: 'На проверке',
  active: 'Активен',
  inactive: 'Неактивен',
  blacklist: 'В черном списке',
};

const userStatusValueByLabel: Record<string, string> = {
  'на проверке': 'review',
  'активен': 'active',
  'неактивен': 'inactive',
  'в черном списке': 'blacklist',
  'в чёрном списке': 'blacklist',
};

const statusToneKeyByValue: Record<string, StatusPillTone> = {
  review: 'warning',
  active: 'success',
  inactive: 'neutral',
  blacklist: 'error',
};

export const normalizeAnyStatus = (value: string | null | undefined): string => {
  const normalized = (value ?? '').toLowerCase();
  if (normalized in statusToneKeyByValue) {
    return normalized;
  }
  if (normalized in userStatusValueByLabel) {
    return userStatusValueByLabel[normalized];
  }
  return normalized;
};

export const normalizeUserStatus = (value: string | null | undefined): 'review' | 'active' | 'inactive' | 'blacklist' => {
  const normalized = (value ?? '').toLowerCase();
  if (normalized in userStatusLabelByValue) {
    return normalized as 'review' | 'active' | 'inactive' | 'blacklist';
  }
  return (userStatusValueByLabel[normalized] as 'review' | 'active' | 'inactive' | 'blacklist') ?? 'review';
};

export const toStatusLabel = (value: string | null | undefined): string => {
  const normalized = normalizeAnyStatus(value);
  if (normalized in userStatusLabelByValue) {
    return userStatusLabelByValue[normalized];
  }
  return value ?? '—';
};

export { userStatusLabelByValue, statusToneKeyByValue };

export const UserStatusPill = ({ value }: { value: string | null | undefined }) => {
  const normalized = normalizeAnyStatus(value);
  const tone = statusToneKeyByValue[normalized] ?? 'info';
  return <StatusPill label={toStatusLabel(value)} tone={tone} />;
};

export const InfoRow = ({ label, value }: { label: string; value: string | number | null }) => (
  <Stack spacing={0.2} sx={{ minWidth: 0 }}>
    <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase', letterSpacing: '0.04em' }}>
      {label}
    </Typography>
    <Typography variant="body1" sx={{ fontWeight: 500, color: 'text.primary', overflowWrap: 'anywhere' }}>
      {value ?? '—'}
    </Typography>
  </Stack>
);

export const SourceSection = ({
  title,
  source,
  children,
}: {
  title: string;
  source: string;
  children: ReactNode;
}) => (
  <Box
    sx={{
      border: '1px solid',
      borderColor: 'divider',
      borderRadius: 1,
      p: { xs: 1.4, sm: 1.8 },
      backgroundColor: 'background.paper',
    }}
  >
    <Stack spacing={1.2}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" flexWrap="wrap" rowGap={0.6}>
        <Typography variant="subtitle2" sx={{ fontWeight: 600, color: 'text.primary' }}>
          {title}
        </Typography>
        <Box
          component="span"
          sx={{
            px: 1,
            py: 0.2,
            borderRadius: 99,
            border: '1px solid',
            borderColor: 'divider',
            backgroundColor: 'background.default',
            color: 'text.secondary',
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: '0.03em',
          }}
        >
          {source}
        </Box>
      </Stack>
      {children}
    </Stack>
  </Box>
);

export const dialogPaperSx = (theme: Theme) => ({
  borderRadius: 2,
  px: { xs: 2.5, sm: 3.5 },
  py: { xs: 3, sm: 3.5 },
  backgroundColor: theme.palette.background.default,
  maxHeight: 'min(760px, calc(100vh - 32px))',
  overflow: 'hidden',
  boxShadow: `0 24px 80px ${alpha(theme.palette.common.black, 0.18)}`,
});

export const dialogContentSx = {
  p: 0,
  overflowX: 'hidden',
  overflowY: 'auto',
  scrollbarWidth: 'none',
  '&::-webkit-scrollbar': {
    display: 'none',
  },
};
