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
        email: 'user@example.com',
        preferences: {
          chat: { email: true },
          request: { email: true },
          offer: { email: true },
          system: { email: true }
        }
      }
    });

    await expect(getMyNotificationPreferences()).resolves.toEqual({
      mode: 'email_only',
      emailAvailable: true,
      email: 'user@example.com',
      preferences: {
        chat: { email: true },
        request: { email: true },
        offer: { email: true },
        system: { email: true }
      }
    });
  });

  it('sends updated detailed notification preferences to backend', async () => {
    vi.mocked(fetchJson).mockResolvedValue({
      data: {
        mode: 'custom',
        email_available: true,
        email: 'user@example.com',
        preferences: {
          chat: { email: true },
          request: { email: false },
          offer: { email: false },
          system: { email: true }
        }
      }
    });

    await updateMyNotificationPreferences({
      preferences: {
        chat: { email: true },
        request: { email: false }
      }
    });

    expect(fetchJson).toHaveBeenCalledWith(
      '/api/v1/users/me/notification-preferences',
      {
        method: 'PUT',
        body: JSON.stringify({
          preferences: {
            chat: { email: true },
            request: { email: false }
          }
        })
      },
      'Не удалось сохранить настройки уведомлений'
    );
  });
});
