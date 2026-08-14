import { afterEach, describe, expect, it, vi } from 'vitest';

import { fetchJson, setAuthRuntime } from './client';

describe('api client upload reason_code handling', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    setAuthRuntime(null);
  });

  it('prefers upload reason_code message over generic detail fallback', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          detail: 'Произошла ошибка. Попробуйте повторить действие.',
          reason_code: 'empty_file',
        }),
        {
          status: 422,
          headers: { 'Content-Type': 'application/json' },
        }
      )
    );

    await expect(
      fetchJson('/api/v1/requests/10/files', { method: 'POST', body: new FormData() }, 'Ошибка прикрепления файла')
    ).rejects.toThrow('Файл пустой.');
  });

  it('prefers upload reason_code message over not-found detail fallback', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          detail: 'Данные не найдены или были удалены.',
          reason_code: 'invalid_pdf',
        }),
        {
          status: 422,
          headers: { 'Content-Type': 'application/json' },
        }
      )
    );

    await expect(
      fetchJson('/api/v1/requests/10/files', { method: 'POST', body: new FormData() }, 'Ошибка прикрепления файла')
    ).rejects.toThrow('PDF-файл поврежден или не читается.');
  });
});
