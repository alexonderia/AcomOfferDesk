import { describe, expect, it, vi } from 'vitest';
import { showBusinessNotificationToast, showSystemToast } from './toastFacade';

describe('toastFacade', () => {
  it('shows system toast at top-center', () => {
    const enqueueSnackbar = vi.fn();

    showSystemToast(
      { enqueueSnackbar },
      {
        severity: 'success',
        message: 'Изменения сохранены',
      }
    );

    expect(enqueueSnackbar).toHaveBeenCalledTimes(1);
    expect(enqueueSnackbar.mock.calls[0][1]).toMatchObject({
      anchorOrigin: { vertical: 'top', horizontal: 'center' },
      variant: 'success',
    });
  });

  it('shows business toast at bottom-right', () => {
    const enqueueSnackbar = vi.fn();

    showBusinessNotificationToast({
      deps: { enqueueSnackbar },
      key: 'notification-1',
      notification: { severity: 'info', title: 'Новое уведомление' },
    });

    expect(enqueueSnackbar).toHaveBeenCalledTimes(1);
    expect(enqueueSnackbar.mock.calls[0][1]).toMatchObject({
      anchorOrigin: { vertical: 'bottom', horizontal: 'right' },
      autoHideDuration: 10000,
    });
  });
});

