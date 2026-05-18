import type { SnackbarKey, VariantType, ProviderContext } from 'notistack';
import type { Notification } from '@features/notifications/model/types';

type ToastSeverity = Extract<VariantType, 'success' | 'info' | 'warning' | 'error'>;

type ShowSystemToastInput = {
  title?: string;
  message: string;
  severity: ToastSeverity;
};

type ShowSystemToastDeps = Pick<ProviderContext, 'enqueueSnackbar'>;

type ShowBusinessToastInput = {
  notification: Pick<Notification, 'severity' | 'title'>;
  key: SnackbarKey;
  deps: Pick<ProviderContext, 'enqueueSnackbar'>;
};

const SYSTEM_TOAST_SUCCESS_INFO_MS = 5_000;
const SYSTEM_TOAST_WARNING_ERROR_MS = 8_000;
const BUSINESS_TOAST_INFO_SUCCESS_MS = 10_000;
const BUSINESS_TOAST_WARNING_ERROR_MS = 14_000;

const getAutoHideDurationBySeverity = (severity: ToastSeverity) =>
  severity === 'warning' || severity === 'error'
    ? SYSTEM_TOAST_WARNING_ERROR_MS
    : SYSTEM_TOAST_SUCCESS_INFO_MS;

const toSafeMessage = (value: unknown, fallback: string) => {
  if (typeof value !== 'string') {
    return fallback;
  }
  const normalized = value.trim();
  return normalized || fallback;
};

export const showSystemToast = ({ enqueueSnackbar }: ShowSystemToastDeps, input: ShowSystemToastInput) => {
  const message = toSafeMessage(input.message, 'Операция завершена');
  const title = toSafeMessage(input.title, '');
  enqueueSnackbar(title ? `${title}: ${message}` : message, {
    variant: input.severity,
    anchorOrigin: { vertical: 'top', horizontal: 'center' },
    autoHideDuration: getAutoHideDurationBySeverity(input.severity),
    preventDuplicate: true,
  });
};

export const showErrorToast = (deps: ShowSystemToastDeps, message: unknown) => {
  showSystemToast(deps, {
    severity: 'error',
    message: toSafeMessage(message, 'Не удалось выполнить действие'),
  });
};

export const showSuccessToast = (deps: ShowSystemToastDeps, message: unknown) => {
  showSystemToast(deps, {
    severity: 'success',
    message: toSafeMessage(message, 'Действие выполнено'),
  });
};

export const getBusinessToastAutoHideDuration = (
  severity: Pick<Notification, 'severity'>['severity']
): number => (severity === 'error' || severity === 'warning' ? BUSINESS_TOAST_WARNING_ERROR_MS : BUSINESS_TOAST_INFO_SUCCESS_MS);

export const showBusinessNotificationToast = ({ deps, notification, key }: ShowBusinessToastInput) => {
  deps.enqueueSnackbar(notification.title, {
    key,
    persist: false,
    autoHideDuration: getBusinessToastAutoHideDuration(notification.severity),
    anchorOrigin: { vertical: 'bottom', horizontal: 'right' },
  });
};
