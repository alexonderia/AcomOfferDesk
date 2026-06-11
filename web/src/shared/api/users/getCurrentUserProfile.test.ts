import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  getMyNotificationPreferences,
  updateMyNotificationPreferences
} from './getCurrentUserProfile';
import { fetchJson } from '../client';

vi.mock('../client', () => ({
  fetchJson: vi.fn()
}));

describe('getCurrentUserProfile notification preferences api', () => {
  beforeEach(() => {
    vi.mocked(fetchJson).mockReset();
  });

  it('maps notification preferences response to frontend shape', async () => {
    vi.mocked(fetchJson).mockResolvedValue({
      data: {
        mode: 'email_only',
        email_available: true,
        max_available: false,
        email: 'user@example.com',
        max_user_id: null
      }
    });

    await expect(getMyNotificationPreferences()).resolves.toEqual({
      mode: 'email_only',
      emailAvailable: true,
      maxAvailable: false,
      email: 'user@example.com',
      maxUserId: null
    });
  });

  it('sends updated notification mode to backend', async () => {
    vi.mocked(fetchJson).mockResolvedValue({
      data: {
        mode: 'max_only',
        email_available: true,
        max_available: true,
        email: 'user@example.com',
        max_user_id: 'max-42'
      }
    });

    await updateMyNotificationPreferences({ mode: 'max_only' });

    expect(fetchJson).toHaveBeenCalledWith(
      '/api/v1/users/me/notification-preferences',
      {
        method: 'PUT',
        body: JSON.stringify({ mode: 'max_only' })
      },
      'Не удалось сохранить настройки уведомлений'
    );
  });
});
