import VisibilityOutlined from '@mui/icons-material/VisibilityOutlined';
import VisibilityOffOutlined from '@mui/icons-material/VisibilityOffOutlined';
import { IconButton, InputAdornment, TextField, Tooltip, type TextFieldProps } from '@mui/material';
import { forwardRef, useState } from 'react';

export const PasswordTextField = forwardRef<HTMLDivElement, Omit<TextFieldProps, 'type'>>(
  function PasswordTextField({ InputProps, label, disabled, ...props }, ref) {
    const [visible, setVisible] = useState(false);
    const fieldLabel = typeof label === 'string' ? label.toLowerCase() : 'пароль';
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
