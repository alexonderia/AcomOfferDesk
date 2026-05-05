import type { UnavailabilityPeriodInfo } from '../model/types';
import { UNAVAILABILITY_REASON_OPTIONS } from '../model/constants';

const reasonLabels = new Map<string, string>(
  UNAVAILABILITY_REASON_OPTIONS.map((option) => [option.value, option.label])
);

export const formatUnavailabilityDate = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  }).format(date);
};

export const getUnavailabilityStatusLabel = (status: string) => reasonLabels.get(status) ?? status;

export const getUnavailabilityTooltip = (period: UnavailabilityPeriodInfo) => {
  const statusLabel = getUnavailabilityStatusLabel(period.status);
  const startedAt = formatUnavailabilityDate(period.startedAt);
  const endedAt = formatUnavailabilityDate(period.endedAt);
  return `${statusLabel}: ${startedAt} - ${endedAt}`;
};
