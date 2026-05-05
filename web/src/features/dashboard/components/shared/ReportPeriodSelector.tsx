import ExpandLessRoundedIcon from "@mui/icons-material/ExpandLessRounded";
import ExpandMoreRoundedIcon from "@mui/icons-material/ExpandMoreRounded";
import {
  Box,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Popover,
  Select,
  Stack,
  Typography,
} from "@mui/material";
import { useState, type MouseEvent } from "react";
import { DatePickerField } from "@shared/components/DatePickerField";

type PeriodMode = "year" | "month" | "range";

const monthOptions = [
  { value: "01", label: "Январь" },
  { value: "02", label: "Февраль" },
  { value: "03", label: "Март" },
  { value: "04", label: "Апрель" },
  { value: "05", label: "Май" },
  { value: "06", label: "Июнь" },
  { value: "07", label: "Июль" },
  { value: "08", label: "Август" },
  { value: "09", label: "Сентябрь" },
  { value: "10", label: "Октябрь" },
  { value: "11", label: "Ноябрь" },
  { value: "12", label: "Декабрь" },
];

const getMonthBounds = (monthValue: string) => {
  const [rawYear, rawMonth] = monthValue.split("-");
  const year = Number.parseInt(rawYear ?? "", 10);
  const month = Number.parseInt(rawMonth ?? "", 10);
  if (!Number.isFinite(year) || !Number.isFinite(month) || month < 1 || month > 12) {
    return null;
  }
  const monthStart = `${year}-${String(month).padStart(2, "0")}-01`;
  const lastDay = new Date(year, month, 0).getDate();
  const monthEnd = `${year}-${String(month).padStart(2, "0")}-${String(lastDay).padStart(2, "0")}`;
  return { monthStart, monthEnd };
};

const getYearBounds = (yearValue: string) => {
  const year = Number.parseInt(yearValue, 10);
  if (!Number.isFinite(year)) {
    return null;
  }
  return {
    yearStart: `${year}-01-01`,
    yearEnd: `${year}-12-31`,
  };
};

const toRuDate = (value: string) => {
  const parsed = new Date(`${value}T00:00:00`);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleDateString("ru-RU");
};

const buildPeriodButtonLabel = (dateFrom: string, dateTo: string) => {
  const yearFrom = dateFrom.slice(0, 4);
  const yearTo = dateTo.slice(0, 4);
  const monthFrom = dateFrom.slice(5, 7);
  const monthTo = dateTo.slice(5, 7);

  if (
    yearFrom === yearTo &&
    dateFrom === `${yearFrom}-01-01` &&
    dateTo === `${yearFrom}-12-31`
  ) {
    return `${yearFrom} год`;
  }

  if (yearFrom === yearTo && monthFrom === monthTo) {
    const month = monthOptions.find((item) => item.value === monthFrom)?.label ?? monthFrom;
    return `${month} ${yearFrom}`;
  }

  return `${toRuDate(dateFrom)} — ${toRuDate(dateTo)}`;
};

type ReportPeriodSelectorProps = {
  dateFrom: string;
  dateTo: string;
  onDateFromChange: (value: string) => void;
  onDateToChange: (value: string) => void;
  minWidth?: number;
};

export const ReportPeriodSelector = ({
  dateFrom,
  dateTo,
  onDateFromChange,
  onDateToChange,
  minWidth = 390,
}: ReportPeriodSelectorProps) => {
  const [periodAnchorEl, setPeriodAnchorEl] = useState<HTMLElement | null>(null);
  const [periodMode, setPeriodMode] = useState<PeriodMode>("month");
  const [draftDateFrom, setDraftDateFrom] = useState(dateFrom);
  const [draftDateTo, setDraftDateTo] = useState(dateTo);
  const isPeriodOpen = Boolean(periodAnchorEl);
  const currentYear = new Date().getFullYear();
  const selectedYear = draftDateFrom?.slice(0, 4) || String(currentYear);
  const selectedMonth = draftDateFrom?.slice(5, 7) || "01";
  const yearOptions = Array.from({ length: 13 }, (_, index) =>
    String(currentYear - 8 + index),
  );
  const selectedPeriodLabel = buildPeriodButtonLabel(dateFrom, dateTo);

  const openPeriodPopover = (event: MouseEvent<HTMLElement>) => {
    setDraftDateFrom(dateFrom);
    setDraftDateTo(dateTo);
    setPeriodAnchorEl(event.currentTarget);
  };

  const handlePeriodModeChange = (nextMode: PeriodMode) => {
    setPeriodMode(nextMode);
    if (nextMode === "year") {
      const bounds = getYearBounds(selectedYear);
      if (bounds) {
        setDraftDateFrom(bounds.yearStart);
        setDraftDateTo(bounds.yearEnd);
      }
      return;
    }
    if (nextMode === "month") {
      const bounds = getMonthBounds(`${selectedYear}-${selectedMonth}`);
      if (bounds) {
        setDraftDateFrom(bounds.monthStart);
        setDraftDateTo(bounds.monthEnd);
      }
    }
  };

  const applyPeriodSelection = () => {
    onDateFromChange(draftDateFrom);
    onDateToChange(draftDateTo);
    setPeriodAnchorEl(null);
  };

  return (
    <Box sx={{ minWidth: { xs: "100%", sm: minWidth } }}>
      <Button
        fullWidth
        variant="outlined"
        onClick={openPeriodPopover}
        sx={{
          justifyContent: "space-between",
          minHeight: 40,
          borderRadius: (theme) => `${theme.acomShape.controlRadius}px`,
          textTransform: "none",
          fontWeight: 400,
          color: "#111111",
          bgcolor: "rgba(255,255,255,0.96)",
          borderColor: "rgba(0, 0, 0, 0.23)",
          px: 1.75,
          "&:hover": {
            color: "#111111",
            bgcolor: "rgba(255,255,255,0.96)",
            borderColor: "primary.main",
          },
        }}
      >
        {selectedPeriodLabel}
        {isPeriodOpen ? <ExpandLessRoundedIcon fontSize="small" /> : <ExpandMoreRoundedIcon fontSize="small" />}
      </Button>
      <Popover
        open={isPeriodOpen}
        anchorEl={periodAnchorEl}
        onClose={() => setPeriodAnchorEl(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "left" }}
        transformOrigin={{ vertical: "top", horizontal: "left" }}
        slotProps={{
          paper: {
            sx: {
              p: 2.25,
              mt: 0.75,
              minWidth: { xs: 320, sm: 440 },
              borderRadius: (theme) => `${theme.acomShape.controlRadius}px`,
              border: "1px solid rgba(148, 163, 184, 0.28)",
              boxShadow: "0 16px 40px rgba(15, 23, 42, 0.16)",
            },
          },
        }}
      >
        <Stack spacing={1.5}>
          <Stack spacing={0.45}>
            <Typography variant="body2" fontWeight={700}>
              Период отчета
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Выберите год, месяц или произвольный диапазон дат
            </Typography>
          </Stack>
          <Stack direction="row" spacing={0.8} useFlexGap flexWrap="wrap">
            <Button
              size="small"
              variant={periodMode === "year" ? "contained" : "outlined"}
              onClick={() => handlePeriodModeChange("year")}
              sx={{ borderRadius: "999px", px: 1.4 }}
            >
              За год
            </Button>
            <Button
              size="small"
              variant={periodMode === "month" ? "contained" : "outlined"}
              onClick={() => handlePeriodModeChange("month")}
              sx={{ borderRadius: "999px", px: 1.4 }}
            >
              Месяц/год
            </Button>
            <Button
              size="small"
              variant={periodMode === "range" ? "contained" : "outlined"}
              onClick={() => handlePeriodModeChange("range")}
              sx={{ borderRadius: "999px", px: 1.4 }}
            >
              Диапазон дат
            </Button>
          </Stack>

          {periodMode === "year" ? (
            <FormControl size="small" sx={{ maxWidth: 220 }}>
              <InputLabel id="report-period-year-only-label">Год</InputLabel>
              <Select
                labelId="report-period-year-only-label"
                label="Год"
                value={selectedYear}
                onChange={(event) => {
                  const bounds = getYearBounds(event.target.value);
                  if (!bounds) {
                    return;
                  }
                  setDraftDateFrom(bounds.yearStart);
                  setDraftDateTo(bounds.yearEnd);
                }}
              >
                {yearOptions.map((year) => (
                  <MenuItem key={year} value={year}>
                    {year}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          ) : periodMode === "month" ? (
            <Stack direction="row" spacing={1.1}>
              <FormControl size="small" sx={{ flex: 1 }}>
                <InputLabel id="report-period-year-label">Год</InputLabel>
                <Select
                  labelId="report-period-year-label"
                  label="Год"
                  value={selectedYear}
                  onChange={(event) => {
                    const bounds = getMonthBounds(
                      `${event.target.value}-${selectedMonth}`,
                    );
                    if (!bounds) {
                      return;
                    }
                    setDraftDateFrom(bounds.monthStart);
                    setDraftDateTo(bounds.monthEnd);
                  }}
                >
                  {yearOptions.map((year) => (
                    <MenuItem key={year} value={year}>
                      {year}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <FormControl size="small" sx={{ flex: 1.25 }}>
                <InputLabel id="report-period-month-label">Месяц</InputLabel>
                <Select
                  labelId="report-period-month-label"
                  label="Месяц"
                  value={selectedMonth}
                  onChange={(event) => {
                    const bounds = getMonthBounds(
                      `${selectedYear}-${event.target.value}`,
                    );
                    if (!bounds) {
                      return;
                    }
                    setDraftDateFrom(bounds.monthStart);
                    setDraftDateTo(bounds.monthEnd);
                  }}
                >
                  {monthOptions.map((month) => (
                    <MenuItem key={month.value} value={month.value}>
                      {month.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Stack>
          ) : (
            <Stack direction="row" spacing={1.1}>
              <DatePickerField
                label="С"
                value={draftDateFrom}
                onChange={(value) => {
                  if (!value) {
                    return;
                  }
                  setDraftDateFrom(value);
                }}
                allowClear={false}
                showDropdownIcon
                sx={{ flex: 1 }}
              />
              <DatePickerField
                label="По"
                value={draftDateTo}
                onChange={(value) => {
                  if (!value) {
                    return;
                  }
                  setDraftDateTo(value);
                }}
                allowClear={false}
                showDropdownIcon
                sx={{ flex: 1 }}
              />
            </Stack>
          )}
          <Stack direction="row" justifyContent="flex-end" sx={{ pt: 0.25 }}>
            <Button size="small" onClick={applyPeriodSelection}>
              Готово
            </Button>
          </Stack>
        </Stack>
      </Popover>
    </Box>
  );
};
