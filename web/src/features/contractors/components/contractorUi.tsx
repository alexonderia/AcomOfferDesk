import { Typography } from '@mui/material';
import { formatRuPhone } from '@shared/lib/phone';
import { StatusPill as BaseStatusPill } from '@shared/ui/StatusPill';
import { normalizeAnyStatus, toStatusLabel, userStatusLabelByValue } from '@features/admin/components/UserCardPrimitives';

const contractorStatusToneByValue: Record<string, 'success' | 'warning' | 'error' | 'info' | 'neutral'> = {
  review: 'warning',
  active: 'success',
  inactive: 'neutral',
  blacklist: 'error',
  approved: 'success',
  disapproved: 'error',
};

export const formatPhoneForView = (value: string | null | undefined) => {
  if (!value) {
    return null;
  }
  return formatRuPhone(value) || value;
};

export const ContractorStatusPill = ({ value }: { value: string | null | undefined }) => (
  <BaseStatusPill label={toStatusLabel(value)} tone={contractorStatusToneByValue[normalizeAnyStatus(value)] ?? 'info'} />
);

export const statusLabelForFilter = (value: string | null | undefined): string => {
  const normalized = (value ?? '').toLowerCase();
  if (normalized in userStatusLabelByValue) {
    return userStatusLabelByValue[normalized as keyof typeof userStatusLabelByValue];
  }
  return value ?? '—';
};

export const ContractorTableCell = ({ value }: { value: string | null | undefined }) => (
  <Typography variant="body2">{value ?? '—'}</Typography>
);

export const statusMemoText = `Статусы users:

1) review
   Пользователь на проверке, доступ не выдан.

2) active
   Пользователь активен, доступ разрешён.

3) inactive
   Пользователь деактивирован, доступ запрещён.

4) blacklist
   Пользователь в чёрном списке, доступ запрещён.`;
