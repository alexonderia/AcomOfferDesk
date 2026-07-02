import { Box, TextField, Typography } from '@mui/material';
import type { Theme } from '@mui/material/styles';
import type { ReactNode } from 'react';
import { DatePickerField } from './DatePickerField';
import { formatDate } from '@shared/lib/formatters';
import { themeTokens } from '@shared/theme/tokens';

const detailFieldSx = {
  width: { xs: '100%', sm: 142 },
  '& .MuiOutlinedInput-root': {
    borderRadius: 999,
    minHeight: 34
  },
  '& .MuiOutlinedInput-input': {
    px: 1.1,
    py: 0.6,
    fontSize: themeTokens.typography.body2FontSize
  }
} as const;

const detailValueTextSx = {
  justifySelf: { xs: 'stretch', sm: 'end' },
  textAlign: { xs: 'left', sm: 'right' },
  fontWeight: 500,
  lineHeight: 1.3
} as const;

type ResponsibleContact = {
  fullName?: string | null;
  phone?: string | null;
  mail?: string | null;
};

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
  responsibleContact?: ResponsibleContact | null;
  responsibleContactHighlighted?: boolean;
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

const panelSx = (theme: Theme, highlighted = false) => ({
  border: `1px solid ${highlighted ? theme.palette.primary.main : theme.palette.divider}`,
  borderRadius: `${theme.acomShape.controlRadius}px`,
  overflow: 'hidden',
  backgroundColor: theme.palette.background.paper,
  p: 0.8,
  boxShadow: '0 1px 3px rgba(17, 24, 39, 0.05)',
  transition: theme.transitions.create(['border-color', 'box-shadow'], {
    duration: theme.transitions.duration.shorter
  })
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
    onFinalAmountChange,
    responsibleContact,
    responsibleContactHighlighted = false
  } = value;

  const hasResponsibleContact = Boolean(
    responsibleContact?.fullName || responsibleContact?.phone || responsibleContact?.mail
  );

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
          fontSize: themeTokens.typography.body2FontSize
        }
      }}
    />
  ) : (
    <Typography variant="body2" sx={detailValueTextSx}>{formatDate(deadlineAt)}</Typography>
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
    <Typography variant="body2" sx={detailValueTextSx}>{initialAmountText || '-'}</Typography>
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
    <Typography variant="body2" sx={detailValueTextSx}>{finalAmountText || '-'}</Typography>
  );

  return (
    <Box
      sx={{
        display: 'grid',
        gap: 1.5,
        gridTemplateColumns: {
          xs: '1fr',
          lg: canViewRequestAmounts ? 'repeat(3, minmax(0, 1fr))' : 'repeat(2, minmax(0, 1fr))'
        }
      }}
    >
      {hasResponsibleContact ? (
        <Box
          data-highlighted={responsibleContactHighlighted ? 'true' : 'false'}
          sx={(theme) => panelSx(theme, responsibleContactHighlighted)}
        >
          <DetailRow
            label="ФИО"
            value={<Typography variant="body2" sx={detailValueTextSx}>{responsibleContact?.fullName || '-'}</Typography>}
          />
          <DetailRow
            label="Телефон"
            value={<Typography variant="body2" sx={detailValueTextSx}>{responsibleContact?.phone || '-'}</Typography>}
          />
          <DetailRow
            label="E-mail"
            value={<Typography variant="body2" sx={detailValueTextSx}>{responsibleContact?.mail || '-'}</Typography>}
            divider={false}
          />
        </Box>
      ) : null}
      <Box sx={(theme) => panelSx(theme)}>
        <DetailRow label="Создана" value={<Typography variant="body2" sx={detailValueTextSx}>{formatDate(createdAt)}</Typography>} />
        <DetailRow label="Закрыта" value={<Typography variant="body2" sx={detailValueTextSx}>{formatDate(closedAt)}</Typography>} />
        <DetailRow
          label="Дедлайн сбора КП"
          value={deadlineField}
          divider={!canViewRequestAmounts && showOfferId}
        />
        {!canViewRequestAmounts && showOfferId ? <DetailRow label="Номер КП" value={offerField} divider={false} /> : null}
      </Box>
      {canViewRequestAmounts ? (
        <Box sx={(theme) => panelSx(theme)}>
          <DetailRow label="Сумма по ТЗ, руб." value={initialAmountField} />
          <DetailRow label="Итоговая сумма, руб." value={finalAmountField} />
          {showOfferId ? <DetailRow label="Номер КП" value={offerField} divider={false} /> : null}
        </Box>
      ) : null}
    </Box>
  );
};
