import { useCallback, useState } from 'react';

/** Controls when manual (non react-hook-form) fields should show validation errors. */
export const useLiveFieldVisibility = () => {
  const [submitAttempted, setSubmitAttempted] = useState(false);
  const [touchedFields, setTouchedFields] = useState<Partial<Record<string, boolean>>>({});

  const markTouched = useCallback((field: string) => {
    setTouchedFields((prev) => ({ ...prev, [field]: true }));
  }, []);

  const shouldShowError = useCallback(
    (field: string, error: string | null | undefined) =>
      Boolean(error) && (submitAttempted || Boolean(touchedFields[field])),
    [submitAttempted, touchedFields]
  );

  const markSubmitAttempted = useCallback(() => {
    setSubmitAttempted(true);
  }, []);

  const resetVisibility = useCallback(() => {
    setSubmitAttempted(false);
    setTouchedFields({});
  }, []);

  return {
    markTouched,
    shouldShowError,
    markSubmitAttempted,
    resetVisibility,
  };
};
