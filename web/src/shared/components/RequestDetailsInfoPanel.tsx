import type { ReactNode } from 'react';
import { Box, TextField, Typography } from '@mui/material';
import type { Theme } from '@mui/material/styles';
import { DatePickerField } from './DatePickerField';
import { formatDate } from '@shared/lib/formatters';

const detailFieldSx = {
  width: { xs: '100%', sm: 142 },
  '& .MuiOutlinedInput-root': {
    borderRadius: 999,
    minHeight: 34
  },
  '& .MuiOutlinedInput-input': {
    px: 1.1,
    py: 0.6,
    fontSize: 14
  }
} as const;

const detailValueTextSx = {
  justifySelf: { xs: 'stretch', sm: 'end' },
  textAlign: { xs: 'left', sm: 'right' },
  fontWeight: 500,
  fontSize: 14,
  lineHeight: 1.3
} as const;

type RequestDetailsInfoValue = {
  createdAt: string | null;
  closedAt: string | null;
  deadlineAt: string | null;
  offerId: string;
  showOfferId?: boolean;
  canViewRequestAmounts: boolean;
  initialAmountText?: string;
  finalAmountText?: string;
  isEditMode?: boolean;
  canEditRequest?: boolean;
  deadlineInputValue?: string;
  onDeadlineChange?: (value: string) => void;
  initialAmountInputValue?: string;
  finalAmountInputValue?: string;
  onInitialAmountChange?: (value: string) => void;
  onFinalAmountChange?: (value: string) => void;
};

type RequestDetailsInfoPanelProps = {
  value: RequestDetailsInfoValue;
};

const DetailRow = ({ label, value, divider = true }: { label: string; value: ReactNode; divider?: boolean }) => (
  <Box
    sx={(theme) => ({
      display: 'grid',
      gridTemplateColumns: '1fr auto',
      alignItems: 'center',
      gap: 1,
      px: 1.25,
      py: 0.8,
      borderBottom: divider ? `1px solid ${theme.palette.divider}` : 'none'
    })}
  >
    <Typography variant="caption" color="text.secondary" sx={{ letterSpacing: 0.2 }}>
      {label}
    </Typography>
    <Box sx={{ justifySelf: { xs: 'stretch', sm: 'end' }, display: 'flex' }}>{value}</Box>
  </Box>
);

const panelSx = (theme: Theme) => ({
  border: `1px solid ${theme.palette.divider}`,
  borderRadius: `${theme.acomShape.controlRadius}px`,
  overflow: 'hidden',
  backgroundColor: theme.palette.background.paper,
  p: 0.8,
  boxShadow: '0 1px 3px rgba(17, 24, 39, 0.05)'
});

export const RequestDetailsInfoPanel = ({ value }: RequestDetailsInfoPanelProps) => {
  const {
    createdAt,
    closedAt,
    deadlineAt,
    offerId,
    showOfferId = true,
    canViewRequestAmounts,
    initialAmountText = '-',
    finalAmountText = '-',
    isEditMode = false,
    canEditRequest = false,
    deadlineInputValue = '',
    onDeadlineChange,
    initialAmountInputValue = '',
    finalAmountInputValue = '',
    onInitialAmountChange,
    onFinalAmountChange
  } = value;

  const offerField = (
    <TextField
      size="small"
      value={offerId}
      InputProps={{ readOnly: true }}
      sx={detailFieldSx}
    />
  );

  const deadlineField = isEditMode && canEditRequest && onDeadlineChange ? (
    <DatePickerField
      value={deadlineInputValue}
      onChange={onDeadlineChange}
      showDropdownIcon={false}
      allowClear={false}
      minWidth={detailFieldSx.width}
      sx={{
        '& .MuiInputBase-root': {
          borderRadius: 999,
          minHeight: 34
        },
        '& .MuiInputBase-input': {
          px: 1.1,
          py: 0.6,
          fontSize: 14
        }
      }}
    />
  ) : (
    <Typography sx={detailValueTextSx}>{formatDate(deadlineAt)}</Typography>
  );

  const initialAmountField = isEditMode && canEditRequest && onInitialAmountChange ? (
    <TextField
      size="small"
      value={initialAmountInputValue}
      onChange={(event) => onInitialAmountChange(event.target.value)}
      inputProps={{ min: 0, step: '0.01', inputMode: 'decimal' }}
      sx={detailFieldSx}
    />
  ) : (
    <Typography sx={detailValueTextSx}>{initialAmountText || '-'}</Typography>
  );

  const finalAmountField = isEditMode && canEditRequest && onFinalAmountChange ? (
    <TextField
      size="small"
      value={finalAmountInputValue}
      onChange={(event) => onFinalAmountChange(event.target.value)}
      inputProps={{ min: 0, step: '0.01', inputMode: 'decimal' }}
      sx={detailFieldSx}
    />
  ) : (
    <Typography sx={detailValueTextSx}>{finalAmountText || '-'}</Typography>
  );

  return (
    <Box
      sx={{
        display: 'grid',
        gap: 1.5,
        gridTemplateColumns: { xs: '1fr', md: canViewRequestAmounts ? '1fr 1fr' : '1fr' }
      }}
    >
      <Box sx={panelSx}>
        <DetailRow label="Создана" value={<Typography sx={detailValueTextSx}>{formatDate(createdAt)}</Typography>} />
        <DetailRow label="Закрыта" value={<Typography sx={detailValueTextSx}>{formatDate(closedAt)}</Typography>} />
        <DetailRow
          label="Дедлайн сбора КП"
          value={deadlineField}
          divider={!canViewRequestAmounts && showOfferId}
        />
        {!canViewRequestAmounts && showOfferId ? <DetailRow label="Номер КП" value={offerField} divider={false} /> : null}
      </Box>
      {canViewRequestAmounts ? (
        <Box sx={panelSx}>
          <DetailRow label="Сумма по ТЗ, руб." value={initialAmountField} />
          <DetailRow label="Итоговая сумма, руб." value={finalAmountField} />
          {showOfferId ? <DetailRow label="Номер КП" value={offerField} divider={false} /> : null}
        </Box>
      ) : null}
    </Box>
  );
};
