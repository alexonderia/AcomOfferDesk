import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { useRequestEmailReview } from './useRequestEmailReview';
import type { RequestEmailPreview } from '@shared/api/requests/previewRequestEmails';

vi.mock('@shared/theme/documentFonts', () => ({ documentFontStyles: '' }));

describe('useRequestEmailReview', () => {
  it('aborts a pending preview on navigation and ignores its late result', async () => {
    const { result, rerender } = renderHook(({ id }) => useRequestEmailReview<string>(id), { initialProps: { id: 'first' } });
    let finish!: (preview: RequestEmailPreview) => void;
    let signal!: AbortSignal;
    let pending!: Promise<void>;
    act(() => {
      pending = result.current.prepareReview('first', (input) => {
        signal = input;
        return new Promise(resolve => { finish = resolve; });
      });
    });
    expect(result.current.isLoadingReview).toBe(true);
    rerender({ id: 'second' });
    expect(signal.aborted).toBe(true);
    expect(result.current.isLoadingReview).toBe(false);
    await act(async () => {
      await result.current.prepareReview('second', async () => ({ messages: [], warnings: ['Новая проверка'] }));
    });
    await act(async () => {
      finish({ messages: [], warnings: [] });
      await pending;
    });
    expect(result.current.review?.snapshot).toBe('second');
    expect(result.current.review?.preview.warnings).toEqual(['Новая проверка']);
    rerender({ id: 'third' });
    expect(result.current.review).toBeNull();
  });
});
