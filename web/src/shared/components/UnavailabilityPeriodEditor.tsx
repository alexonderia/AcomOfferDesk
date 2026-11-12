import EventNoteOutlinedIcon from '@mui/icons-material/EventNoteOutlined';
import { InputAdornment, MenuItem, Stack, TextField } from '@mui/material';
import type { UseFormRegisterReturn } from 'react-hook-form';
import { DatePickerField } from './DatePickerField';
import { RequiredFieldLabel } from './forms/RequiredFieldLabel';

export const UNAVAILABILITY_REASON_OPTIONS = [
  { value: 'sick', label: 'Больничный' },
  { value: 'vacation', label: 'Отпуск' },
  { value: 'fired', label: 'Уволен' },
  { value: 'maternity', label: 'Декрет' },
  { value: 'business_trip', label: 'Командировка' },
  { value: 'unavailable', label: 'Недоступен' },
] as const;

type UnavailabilityPeriodEditorProps = {
  statusField: UseFormRegisterReturn<'status'>;
  statusValue: string;
  startedAtField: UseFormRegisterReturn<'started_at'>;
  endedAtField: UseFormRegisterReturn<'ended_at'>;
  startedAtValue: string;
  endedAtValue: string;
  onStartedAtChange: (value: string) => void;
  onEndedAtChange: (value: string) => void;
  statusError?: string;
  startedAtError?: string;
  endedAtError?: string;
};

const ReasonIcon = () => (
  <EventNoteOutlinedIcon fontSize="small" sx={{ color: 'text.secondary' }} />
);

const fieldSx = {
  '& .MuiOutlinedInput-root': {
    borderRadius: 2,
    backgroundColor: 'background.paper',
  },
  '& .MuiInputBase-input': {
    fontWeight: 500,
    fontSize: 14,
  },
  '& .MuiFormHelperText-root': {
    ml: 0.5,
  },
} as const;

export const UnavailabilityPeriodEditor = ({
  statusField,
  statusValue,
  startedAtField,
  endedAtField,
  startedAtValue,
  endedAtValue,
  onStartedAtChange,
  onEndedAtChange,
  statusError,
  startedAtError,
  endedAtError,
}: UnavailabilityPeriodEditorProps) => {
  return (
    <Stack spacing={1.5}>
      <input type="hidden" {...startedAtField} />
      <input type="hidden" {...endedAtField} />

      <TextField
        label={<RequiredFieldLabel label="Причина" isValid={UNAVAILABILITY_REASON_OPTIONS.some((option) => option.value === statusValue) && !statusError} />}
        inputProps={{ 'aria-required': true }}
        select
        {...statusField}
        error={Boolean(statusError)}
        helperText={statusError}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <ReasonIcon />
            </InputAdornment>
          ),
        }}
        sx={fieldSx}
      >
        {UNAVAILABILITY_REASON_OPTIONS.map((option) => (
          <MenuItem key={option.value} value={option.value}>
            {option.label}
          </MenuItem>
        ))}
      </TextField>

      <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
        <DatePickerField
          label={<RequiredFieldLabel label="Дата начала" isValid={Boolean(startedAtValue) && !startedAtError} />}
          inputProps={{ 'aria-required': true }}
          value={startedAtValue}
          onChange={onStartedAtChange}
          error={Boolean(startedAtError)}
          helperText={startedAtError}
          fullWidth
        />

        <DatePickerField
          label={<RequiredFieldLabel label="Дата окончания" isValid={Boolean(endedAtValue) && endedAtValue >= startedAtValue && !endedAtError} />}
          inputProps={{ 'aria-required': true }}
          value={endedAtValue}
          onChange={onEndedAtChange}
          error={Boolean(endedAtError)}
          helperText={endedAtError}
          fullWidth
        />
      </Stack>
    </Stack>
  );
};
