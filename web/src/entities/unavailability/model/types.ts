export type UnavailabilityReason =
  | 'sick'
  | 'vacation'
  | 'fired'
  | 'maternity'
  | 'business_trip'
  | 'unavailable';

export type UnavailabilityPeriodView = {
  id: number;
  status: string;
  startedAt: string;
  endedAt: string;
};

export type UnavailabilityPeriodInfo = {
  status: string;
  startedAt: string;
  endedAt: string;
};
