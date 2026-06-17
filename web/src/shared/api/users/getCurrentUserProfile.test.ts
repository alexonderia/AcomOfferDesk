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
        max_user_id: null,
        preferences: {
          chat: { email: true, max: false },
          request: { email: true, max: false },
          offer: { email: true, max: false },
          system: { email: true, max: false }
        }
      }
    });

    await expect(getMyNotificationPreferences()).resolves.toEqual({
      mode: 'email_only',
      emailAvailable: true,
      maxAvailable: false,
      email: 'user@example.com',
      maxUserId: null,
      preferences: {
        chat: { email: true, max: false },
        request: { email: true, max: false },
        offer: { email: true, max: false },
        system: { email: true, max: false }
      }
    });
  });

  it('sends updated detailed notification preferences to backend', async () => {
    vi.mocked(fetchJson).mockResolvedValue({
      data: {
        mode: 'custom',
        email_available: true,
        max_available: true,
        email: 'user@example.com',
        max_user_id: 'max-42',
        preferences: {
          chat: { email: true, max: false },
          request: { email: true, max: true },
          offer: { email: false, max: true },
          system: { email: true, max: false }
        }
      }
    });

    await updateMyNotificationPreferences({
      preferences: {
        chat: { email: true, max: false },
        request: { email: true, max: true }
      }
    });

    expect(fetchJson).toHaveBeenCalledWith(
      '/api/v1/users/me/notification-preferences',
      {
        method: 'PUT',
        body: JSON.stringify({
          preferences: {
            chat: { email: true, max: false },
            request: { email: true, max: true }
          }
        })
      },
      'Не удалось сохранить настройки уведомлений'
    );
  });
});
