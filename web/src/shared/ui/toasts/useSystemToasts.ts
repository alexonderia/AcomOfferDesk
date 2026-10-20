import { useMemo } from 'react';
import { useSnackbar } from 'notistack';
import { showErrorToast, showSuccessToast, showSystemToast } from './toastFacade';

export const useSystemToasts = () => {
  const { enqueueSnackbar, closeSnackbar } = useSnackbar();

  return useMemo(() => ({
    showSystemToast: (input: Parameters<typeof showSystemToast>[1]) =>
      showSystemToast({ enqueueSnackbar, closeSnackbar }, input),
    showErrorToast: (message: unknown) => showErrorToast({ enqueueSnackbar, closeSnackbar }, message),
    showSuccessToast: (message: unknown) => showSuccessToast({ enqueueSnackbar, closeSnackbar }, message),
  }), [closeSnackbar, enqueueSnackbar]);
};
