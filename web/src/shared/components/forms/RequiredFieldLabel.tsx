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
    {isValid ? (
      <CheckCircleRounded
        sx={{ fontSize: 18, color: 'success.main' }}
        titleAccess="Поле заполнено верно"
      />
    ) : (
      <PriorityHighRounded
        sx={{ fontSize: 18, color: 'warning.main' }}
        titleAccess="Обязательное поле"
      />
    )}
  </Box>
);
