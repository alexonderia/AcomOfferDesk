import { describe, expect, it, vi } from 'vitest';

const client = vi.hoisted(() => ({ fetchJson: vi.fn() }));

vi.mock('../client', () => client);

import { requestPasswordReset } from './passwordReset';

describe('requestPasswordReset', () => {
  it('does not attach an existing authenticated browser session to the public request', async () => {
    client.fetchJson.mockResolvedValue({ detail: 'Инструкция отправлена.' });

    await requestPasswordReset(' superadmin ');

    expect(client.fetchJson).toHaveBeenCalledWith(
      '/api/v1/auth/password-reset/request',
      expect.objectContaining({
        method: 'POST',
        credentials: 'omit',
        body: JSON.stringify({ login: 'superadmin' }),
      }),
      expect.any(String),
      false,
    );
  });
});
