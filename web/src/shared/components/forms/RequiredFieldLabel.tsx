import CheckCircleRounded from '@mui/icons-material/CheckCircleRounded';
import PriorityHighRounded from '@mui/icons-material/PriorityHighRounded';
import { Box } from '@mui/material';
import type { ReactNode } from 'react';

type RequiredFieldLabelProps = {
  isValid: boolean;
  label: string;
};

export const RequiredFieldLabel = ({ isValid, label }: RequiredFieldLabelProps): ReactNode => (
  <Box component="span" sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.75 }}>
    <span>{label}</span>
    <Box component="span" aria-hidden="true" title={isValid ? 'Поле заполнено верно' : 'Обязательное поле'} sx={{ display: 'inline-flex', flexShrink: 0 }}>
      {isValid ? (
        <CheckCircleRounded sx={{ fontSize: 18, color: 'success.main' }} />
      ) : (
        <PriorityHighRounded sx={{ fontSize: 18, color: 'warning.main' }} />
      )}
    </Box>
  </Box>
);
