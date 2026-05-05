import CalendarTodayOutlinedIcon from '@mui/icons-material/CalendarTodayOutlined';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import {
  Box,
  Button,
  IconButton,
  InputAdornment,
  Popover,
  Stack,
  TextField,
  Typography,
  type SxProps,
  type Theme,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import { useMemo, useState, type MouseEvent } from 'react';

type DatePickerFieldProps = {
  value: string;
  onChange: (value: string) => void;
  label?: string;
  placeholder?: string;
  error?: boolean;
  helperText?: string;
  fullWidth?: boolean;
  minWidth?: number | string | { xs?: number | string; sm?: number | string };
  showDropdownIcon?: boolean;
  allowClear?: boolean;
  sx?: SxProps<Theme>;
};

const weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];

const formatValue = (date: Date): string => {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, '0');
  const day = `${date.getDate()}`.padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const parseValue = (value: string): Date | null => {
  if (!value) {
    return null;
  }

  const [year, month, day] = value.split('-').map(Number);
  if (!year || !month || !day) {
    return null;
  }

  const parsed = new Date(year, month - 1, day);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  return parsed;
};

const formatDisplay = (value: string, placeholder: string): string => {
  const parsed = parseValue(value);
  return parsed ? parsed.toLocaleDateString('ru-RU') : placeholder;
};

export const DatePickerField = ({
  value,
  onChange,
  label,
  placeholder = 'Выберите дату',
  error = false,
  helperText,
  fullWidth = false,
  minWidth,
  showDropdownIcon = true,
  allowClear = true,
  sx,
}: DatePickerFieldProps) => {
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  const [viewDate, setViewDate] = useState(() => parseValue(value) ?? new Date());
  const [draftValue, setDraftValue] = useState<string>(value);

  const openCalendar = (event: MouseEvent<HTMLElement>) => {
    setViewDate(parseValue(value) ?? new Date());
    setDraftValue(value);
    setAnchorEl(event.currentTarget);
  };

  const closeCalendar = () => setAnchorEl(null);

  const calendarCells = useMemo(() => {
    const year = viewDate.getFullYear();
    const month = viewDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const firstWeekday = (firstDay.getDay() + 6) % 7;
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    const cells: Array<{ date: Date | null }> = [];

    for (let i = 0; i < firstWeekday; i += 1) {
      cells.push({ date: null });
    }

    for (let day = 1; day <= daysInMonth; day += 1) {
      cells.push({ date: new Date(year, month, day) });
    }

    while (cells.length % 7 !== 0) {
      cells.push({ date: null });
    }

    return cells;
  }, [viewDate]);

  return (
    <>
      <TextField
        label={label}
        value={formatDisplay(value, placeholder)}
        error={error}
        helperText={helperText}
        onClick={openCalendar}
        inputProps={{ readOnly: true }}
        fullWidth={fullWidth}
        InputLabelProps={label ? undefined : { shrink: false }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <Box sx={{ display: 'inline-flex', color: 'text.primary' }}>
                <CalendarTodayOutlinedIcon fontSize="small" />
              </Box>
            </InputAdornment>
          ),
          endAdornment: showDropdownIcon ? (
            <InputAdornment position="end">
              <Box sx={{ display: 'inline-flex', color: 'text.secondary' }}>
                <ExpandMoreIcon fontSize="small" />
              </Box>
            </InputAdornment>
          ) : undefined,
        }}
        sx={{
          minWidth,
          cursor: 'pointer',
          '& .MuiInputBase-root': {
            borderRadius: 1,
            backgroundColor: 'background.paper',
            minHeight: 50,
          },
          '& .MuiInputBase-input': {
            cursor: 'pointer',
            fontWeight: 500,
            fontSize: 15,
            py: 1,
          },
          '& .MuiInputAdornment-root': {
            '& .MuiSvgIcon-root': {
              fontSize: 20,
            },
          },
          '& .MuiFormHelperText-root': {
            ml: 0.5,
          },
          ...sx,
        }}
      />

      <Popover
        open={Boolean(anchorEl)}
        anchorEl={anchorEl}
        onClose={closeCalendar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        transformOrigin={{ vertical: 'top', horizontal: 'left' }}
        PaperProps={{
          elevation: 4,
          sx: (theme) => ({
            borderRadius: 1.2,
            p: 2,
            width: 300,
            border: `1px solid ${theme.palette.divider}`,
            backgroundColor: theme.palette.background.default,
          }),
        }}
      >
        <Stack spacing={1.5}>
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography sx={{ fontSize: 18, fontWeight: 600, textTransform: 'capitalize' }}>
              {viewDate.toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' })}
            </Typography>

            <Stack direction="row" spacing={0.5}>
              <IconButton
                size="small"
                onClick={() => setViewDate(new Date(viewDate.getFullYear(), viewDate.getMonth() - 1, 1))}
                aria-label="Предыдущий месяц"
              >
                <ChevronLeftIcon fontSize="small" />
              </IconButton>

              <IconButton
                size="small"
                onClick={() => setViewDate(new Date(viewDate.getFullYear(), viewDate.getMonth() + 1, 1))}
                aria-label="Следующий месяц"
              >
                <ChevronRightIcon fontSize="small" />
              </IconButton>
            </Stack>
          </Stack>

          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 0.5 }}>
            {weekdays.map((weekday) => (
              <Typography
                key={weekday}
                variant="caption"
                align="center"
                sx={{ color: 'text.secondary', fontWeight: 600 }}
              >
                {weekday}
              </Typography>
            ))}

            {calendarCells.map((cell, index) => {
              const cellValue = cell.date ? formatValue(cell.date) : null;
              const isSelected = cellValue !== null && cellValue === draftValue;

              return (
                <Box
                  key={`${index}-${cellValue ?? 'empty'}`}
                  component="button"
                  type="button"
                  onClick={() => setDraftValue(cellValue ?? '')}
                  disabled={!cell.date}
                  sx={(theme) => ({
                    border: 0,
                    bgcolor: isSelected ? alpha(theme.palette.primary.main, 0.14) : 'transparent',
                    color: isSelected ? theme.palette.primary.main : theme.palette.text.primary,
                    width: 34,
                    height: 34,
                    borderRadius: '50%',
                    justifySelf: 'center',
                    cursor: cell.date ? 'pointer' : 'default',
                    fontSize: 14,
                    fontWeight: isSelected ? 600 : 400,
                    transition: theme.transitions.create(['background-color', 'color']),
                    '&:hover': {
                      bgcolor: cell.date ? alpha(theme.palette.primary.main, 0.08) : 'transparent',
                    },
                    '&:disabled': {
                      color: 'transparent',
                    },
                  })}
                >
                  {cell.date?.getDate() ?? ''}
                </Box>
              );
            })}
          </Box>

          <Stack direction="row" spacing={1}>
            {allowClear ? (
              <Button
                fullWidth
                variant="outlined"
                onClick={() => {
                  onChange('');
                  closeCalendar();
                }}
                sx={{ borderRadius: 2, textTransform: 'none' }}
              >
                Очистить
              </Button>
            ) : null}

            <Button
              fullWidth
              variant="contained"
              onClick={() => {
                onChange(draftValue);
                closeCalendar();
              }}
              sx={{ borderRadius: 2, textTransform: 'none', boxShadow: 'none' }}
            >
              Готово
            </Button>
          </Stack>
        </Stack>
      </Popover>
    </>
  );
};
