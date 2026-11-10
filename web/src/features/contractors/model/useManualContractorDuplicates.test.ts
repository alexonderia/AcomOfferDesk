import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { getManualContractorDuplicates, type ManualContractorDuplicate } from '@shared/api/users/getManualContractorDuplicates';
import { useManualContractorDuplicates } from './useManualContractorDuplicates';

vi.mock('@shared/api/users/getManualContractorDuplicates', () => ({ getManualContractorDuplicates: vi.fn() }));

describe('useManualContractorDuplicates', () => {
  beforeEach(() => vi.mocked(getManualContractorDuplicates).mockReset());

  it('debounces changes and searches only the last input', async () => {
    vi.mocked(getManualContractorDuplicates).mockResolvedValue([]);
    const { rerender } = renderHook(({ companyName }) => useManualContractorDuplicates({ open: true, companyName }), {
      initialProps: { companyName: 'Бе' },
    });
    rerender({ companyName: 'Бет' });
    rerender({ companyName: 'Бетон' });
    await waitFor(() => expect(getManualContractorDuplicates).toHaveBeenCalledOnce());
    expect(getManualContractorDuplicates).toHaveBeenCalledWith({ companyName: 'Бетон', inn: '', companyMail: '', requestId: undefined });
  });

  it.each(['clear', 'close', 'request'] as const)('ignores an in-flight response after %s', async (change) => {
    let resolve: (items: ManualContractorDuplicate[]) => void = () => {};
    vi.mocked(getManualContractorDuplicates).mockImplementationOnce(() => new Promise((done) => { resolve = done; }));
    const { result, rerender } = renderHook((props) => useManualContractorDuplicates(props), {
      initialProps: { open: true, companyName: 'Бетон', requestId: 'request-1' },
    });
    await waitFor(() => expect(getManualContractorDuplicates).toHaveBeenCalledOnce());
    rerender({
      open: change !== 'close', companyName: change === 'clear' ? '' : 'Бетон',
      requestId: change === 'request' ? 'request-2' : 'request-1',
    });
    await act(async () => resolve([{ userId: 'stale' } as ManualContractorDuplicate]));
    expect(result.current.duplicates).toEqual([]);
  });

  it('keeps lookup errors distinct from no matches and supports retry', async () => {
    vi.mocked(getManualContractorDuplicates).mockRejectedValueOnce(new Error('Не удалось проверить похожих контрагентов'));
    const { result } = renderHook(() => useManualContractorDuplicates({ open: true, companyName: 'Бетон' }));
    await waitFor(() => expect(result.current.error).toBe('Не удалось проверить похожих контрагентов'));
    vi.mocked(getManualContractorDuplicates).mockResolvedValue([]);
    act(() => result.current.reload());
    await waitFor(() => expect(getManualContractorDuplicates).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBeNull();
  });
});
