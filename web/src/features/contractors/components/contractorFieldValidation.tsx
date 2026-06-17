import CheckCircleOutlineRounded from '@mui/icons-material/CheckCircleOutlineRounded';
import ErrorOutlineRounded from '@mui/icons-material/ErrorOutlineRounded';
import LockOutlined from '@mui/icons-material/LockOutlined';
import { Box, Tooltip } from '@mui/material';
import type { ReactNode } from 'react';

const LOCKED_FIELD_TOOLTIP = 'Поле недоступно для редактирования';

type ContractorFieldValidationIconProps = {
  error?: string;
  showValidIcon?: boolean;
};

export const ContractorFieldLockIcon = () => (
  <Tooltip title={LOCKED_FIELD_TOOLTIP} arrow placement="top">
    <Box
      component="span"
      aria-label={LOCKED_FIELD_TOOLTIP}
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        color: 'text.disabled',
        flexShrink: 0,
        cursor: 'help',
      }}
    >
      <LockOutlined sx={{ fontSize: 18 }} />
    </Box>
  </Tooltip>
);

export const ContractorFieldValidationIcon = ({
  error,
  showValidIcon = false,
}: ContractorFieldValidationIconProps) => {
  if (error) {
    return (
      <Tooltip title={error} arrow placement="top">
        <Box
          component="span"
          aria-label={error}
          sx={{
            display: 'inline-flex',
            alignItems: 'center',
            color: 'error.main',
            flexShrink: 0,
            cursor: 'help',
          }}
        >
          <ErrorOutlineRounded sx={{ fontSize: 18 }} />
        </Box>
      </Tooltip>
    );
  }

  if (showValidIcon) {
    return (
      <Box
        component="span"
        aria-hidden
        sx={{
          display: 'inline-flex',
          alignItems: 'center',
          color: 'success.main',
          flexShrink: 0,
        }}
      >
        <CheckCircleOutlineRounded sx={{ fontSize: 18 }} />
      </Box>
    );
  }

  return null;
};

export const ContractorEditableFieldFrame = ({
  error,
  dirty,
  children,
}: {
  error?: string;
  dirty?: boolean;
  children: ReactNode;
}) => (
  <Box
    sx={{
      display: 'flex',
      alignItems: 'center',
      gap: 0.75,
      minWidth: 0,
      width: '100%',
    }}
  >
    <Box sx={{ minWidth: 0, flex: 1 }}>{children}</Box>
    <ContractorFieldValidationIcon error={error} showValidIcon={Boolean(dirty && !error)} />
  </Box>
);

export const ContractorReadOnlyFieldFrame = ({
  locked = false,
  children,
}: {
  locked?: boolean;
  children: ReactNode;
}) => (
  <Box
    sx={{
      display: 'flex',
      alignItems: 'center',
      gap: 0.75,
      minWidth: 0,
      width: '100%',
    }}
  >
    <Box sx={{ minWidth: 0, flex: 1 }}>{children}</Box>
    {locked ? <ContractorFieldLockIcon /> : null}
  </Box>
);
