import type { UnavailabilityReason } from './types';

export const UNAVAILABILITY_REASON_OPTIONS: Array<{ value: UnavailabilityReason; label: string }> = [
  { value: 'sick', label: 'Больничный' },
  { value: 'vacation', label: 'Отпуск' },
  { value: 'fired', label: 'Уволен' },
  { value: 'maternity', label: 'Декрет' },
  { value: 'business_trip', label: 'Командировка' },
  { value: 'unavailable', label: 'Недоступен' }
];
