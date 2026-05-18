import { useSnackbar } from 'notistack';
import { showErrorToast, showSuccessToast, showSystemToast } from './toastFacade';

export const useSystemToasts = () => {
  const { enqueueSnackbar } = useSnackbar();

  return {
    showSystemToast: (input: Parameters<typeof showSystemToast>[1]) =>
      showSystemToast({ enqueueSnackbar }, input),
    showErrorToast: (message: unknown) => showErrorToast({ enqueueSnackbar }, message),
    showSuccessToast: (message: unknown) => showSuccessToast({ enqueueSnackbar }, message),
  };
};

