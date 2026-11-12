import VisibilityOutlined from '@mui/icons-material/VisibilityOutlined';
import VisibilityOffOutlined from '@mui/icons-material/VisibilityOffOutlined';
import { IconButton, InputAdornment, TextField, Tooltip, type TextFieldProps } from '@mui/material';
import { forwardRef, isValidElement, useState } from 'react';
import { RequiredFieldLabel } from './RequiredFieldLabel';

export const PasswordTextField = forwardRef<HTMLDivElement, Omit<TextFieldProps, 'type'>>(
  function PasswordTextField({ InputProps, label, disabled, ...props }, ref) {
    const [visible, setVisible] = useState(false);
    const labelText = typeof label === 'string'
      ? label
      : isValidElement<{ label: string }>(label) && label.type === RequiredFieldLabel ? label.props.label : 'пароль';
    const fieldLabel = labelText.toLowerCase();
    const actionLabel = `${visible ? 'Скрыть' : 'Показать'} ${fieldLabel}`;

    return (
      <TextField
        {...props}
        ref={ref}
        label={label}
        disabled={disabled}
        type={visible ? 'text' : 'password'}
        InputProps={{
          ...InputProps,
          endAdornment: (
            <>
              {InputProps?.endAdornment}
              <InputAdornment position="end">
                <Tooltip title={actionLabel}>
                  <IconButton
                    type="button"
                    color="primary"
                    edge="end"
                    aria-label={actionLabel}
                    aria-pressed={visible}
                    disabled={disabled}
                    onMouseDown={(event) => event.preventDefault()}
                    onClick={() => setVisible((current) => !current)}
                  >
                    {visible ? <VisibilityOffOutlined /> : <VisibilityOutlined />}
                  </IconButton>
                </Tooltip>
              </InputAdornment>
            </>
          ),
        }}
      />
    );
  },
);
