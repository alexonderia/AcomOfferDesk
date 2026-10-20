import { useEffect, useRef } from 'react';
import type { VariantType } from 'notistack';
import { useSystemToasts } from './useSystemToasts';

type ToastSeverity = Extract<VariantType, 'success' | 'info' | 'warning' | 'error'>;

type UseToastMessageEffectInput = {
  dedupeKey?: string | number | null;
  message: string | null | undefined;
  severity?: ToastSeverity;
};

export const useToastMessageEffect = ({
  dedupeKey,
  message,
  severity = 'error',
}: UseToastMessageEffectInput) => {
  const lastShownKeyRef = useRef<string | number | null>(null);
  const { showErrorToast, showSuccessToast, showSystemToast } = useSystemToasts();

  useEffect(() => {
    if (!message) {
      lastShownKeyRef.current = null;
      return;
    }

    const nextKey = dedupeKey ?? `${severity}:${message}`;
    if (lastShownKeyRef.current === nextKey) {
      return;
    }

    if (severity === 'error') {
      showErrorToast(message);
    } else if (severity === 'success') {
      showSuccessToast(message);
    } else {
      showSystemToast({ severity, message });
    }

    lastShownKeyRef.current = nextKey;
  }, [dedupeKey, message, severity, showErrorToast, showSuccessToast, showSystemToast]);
};
