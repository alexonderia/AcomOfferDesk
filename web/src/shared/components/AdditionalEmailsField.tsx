import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import { forwardRef, useImperativeHandle, useState } from 'react';
import {
  Box,
  Button,
  Chip,
  IconButton,
  InputAdornment,
  Stack,
  TextField,
  Typography,
  type SxProps,
  type Theme,
} from '@mui/material';
import { isValidAdditionalEmail, mergeAdditionalEmails, splitAdditionalEmails } from '@shared/lib/additionalEmails';

export type AdditionalEmailsFieldHandle = {
  commitPendingInput: () => string[] | null;
};

type AdditionalEmailsFieldProps = {
  emails: string[];
  onChange: (emails: string[]) => void;
  disabled?: boolean;
  label?: string;
  description?: string;
  placeholder?: string;
  helperText?: string;
  hideHeader?: boolean;
  addButtonVariant?: 'button' | 'icon';
  containerSx?: SxProps<Theme>;
  textFieldSx?: SxProps<Theme>;
};

export const AdditionalEmailsField = forwardRef<AdditionalEmailsFieldHandle, AdditionalEmailsFieldProps>(
  (
    {
      emails,
      onChange,
      disabled = false,
      label = 'Дополнительные e-mail для рассылки',
      description = 'Можно добавить адреса, которых нет в базе верифицированных контрагентов.',
      placeholder = 'name@example.com',
      helperText = 'Введите один или несколько email через запятую и нажмите Enter или кнопку добавления.',
      hideHeader = false,
      addButtonVariant = 'button',
      containerSx,
      textFieldSx,
    },
    ref
  ) => {
    const [inputValue, setInputValue] = useState('');
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    const commitPendingInput = () => {
      const parsedEmails = splitAdditionalEmails(inputValue);
      if (parsedEmails.length === 0) {
        setErrorMessage(null);
        return emails;
      }

      for (const email of parsedEmails) {
        if (!isValidAdditionalEmail(email)) {
          setErrorMessage(`Некорректный email: ${email}`);
          return null;
        }
      }

      const nextEmails = mergeAdditionalEmails(emails, parsedEmails);
      onChange(nextEmails);
      setInputValue('');
      setErrorMessage(null);
      return nextEmails;
    };

    useImperativeHandle(
      ref,
      () => ({
        commitPendingInput,
      }),
      [commitPendingInput]
    );

    return (
      <Stack spacing={1.5} mt={3} sx={containerSx}>
        {!hideHeader ? (
          <>
            <Typography variant="subtitle1" fontWeight={600}>
              {label}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {description}
            </Typography>
          </>
        ) : null}

        <Stack
          direction={{ xs: 'column', sm: addButtonVariant === 'button' ? 'row' : 'column' }}
          spacing={1.5}
          alignItems={{ xs: 'stretch', sm: 'flex-start' }}
        >
          <TextField
            fullWidth
            placeholder={placeholder}
            value={inputValue}
            disabled={disabled}
            error={Boolean(errorMessage)}
            helperText={errorMessage ?? helperText}
            InputProps={
              addButtonVariant === 'icon'
                ? {
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          edge="end"
                          disabled={disabled}
                          aria-label="Добавить email"
                          onClick={() => {
                            commitPendingInput();
                          }}
                          sx={{ color: 'primary.main' }}
                        >
                          <AddCircleOutlineIcon />
                        </IconButton>
                      </InputAdornment>
                    ),
                  }
                : undefined
            }
            onChange={(event) => {
              setInputValue(event.target.value);
              if (errorMessage) {
                setErrorMessage(null);
              }
            }}
            onKeyDown={(event) => {
              if (event.key === 'Enter' || event.key === ',') {
                event.preventDefault();
                commitPendingInput();
              }
            }}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
                backgroundColor: 'background.paper',
              },
              ...textFieldSx,
            }}
          />

          {addButtonVariant === 'button' ? (
            <Button
              variant="outlined"
              disabled={disabled}
              onClick={() => {
                commitPendingInput();
              }}
              sx={{
                minWidth: { sm: 132 },
                borderRadius: 2,
                textTransform: 'none',
                px: 3,
              }}
            >
              Добавить
            </Button>
          ) : null}
        </Stack>

        {emails.length > 0 ? (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {emails.map((email) => (
              <Chip
                key={email}
                label={email}
                onDelete={disabled ? undefined : () => onChange(emails.filter((item) => item !== email))}
                variant="outlined"
                sx={{
                  maxWidth: '100%',
                  borderRadius: 2,
                  backgroundColor: 'background.paper',
                  '& .MuiChip-label': {
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  },
                }}
              />
            ))}
          </Box>
        ) : null}
      </Stack>
    );
  }
);

AdditionalEmailsField.displayName = 'AdditionalEmailsField';
