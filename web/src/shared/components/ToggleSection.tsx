import type { ChangeEvent, ReactNode } from 'react';
import { Collapse, FormControlLabel, Stack, Switch, Typography, type SwitchProps } from '@mui/material';

type ToggleSectionProps = {
  title: string;
  checked: boolean;
  onChange: (event: ChangeEvent<HTMLInputElement>, checked: boolean) => void;
  description: string;
  children: ReactNode;
  disabled?: boolean;
};

const StyledSwitch = (props: SwitchProps) => (
  <Switch
    {...props}
    sx={{
      width: 46,
      height: 28,
      p: 0,
      '& .MuiSwitch-switchBase': {
        p: '4px',
        '&.Mui-checked': {
          transform: 'translateX(18px)',
          color: '#fff',
          '& + .MuiSwitch-track': {
            opacity: 1,
            backgroundColor: 'primary.main',
            borderColor: 'primary.main',
          },
        },
      },
      '& .MuiSwitch-thumb': {
        width: 20,
        height: 20,
        boxShadow: 'none',
      },
      '& .MuiSwitch-track': {
        borderRadius: '999px',
        opacity: 1,
        backgroundColor: 'action.selected',
        border: '1px solid',
        borderColor: 'divider',
      },
    }}
  />
);

export const ToggleSection = ({
  title,
  checked,
  onChange,
  description,
  children,
  disabled = false,
}: ToggleSectionProps) => (
  <Stack spacing={1.25}>
    <FormControlLabel
      disabled={disabled}
      sx={{ m: 0, alignItems: 'center', gap: 1.5 }}
      control={<StyledSwitch checked={checked} onChange={onChange} disabled={disabled} />}
      label={
        <Typography
          variant="subtitle1"
          fontWeight={600}
          lineHeight={1.2}
          color={disabled ? 'text.disabled' : 'text.primary'}
        >
          {title}
        </Typography>
      }
    />

    <Collapse in={checked} unmountOnExit>
      <Stack spacing={1.25}>
        <Typography variant="body1" lineHeight={1.35} color={disabled ? 'text.disabled' : 'text.primary'}>
          {description}
        </Typography>
        {children}
      </Stack>
    </Collapse>
  </Stack>
);
