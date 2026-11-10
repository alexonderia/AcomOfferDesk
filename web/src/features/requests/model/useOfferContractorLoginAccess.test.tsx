import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { ContractorLoginAccess } from '@shared/api/contractors/getContractorLoginAccess';
import type { RequestDetailsOffer } from '@shared/api/requests/getRequestDetails';
import { useOfferContractorLoginAccess } from './useOfferContractorLoginAccess';

const getAccess = vi.fn();
vi.mock('@shared/api/contractors/getContractorLoginAccess', () => ({
  getContractorLoginAccess: (...args: unknown[]) => getAccess(...args),
}));
const offer = (id: string, allowed = true) => ({
  contractor_user_id: id, actions: { view_contractor_info: allowed },
} as RequestDetailsOffer);
const access = (id: string): ContractorLoginAccess => ({ user_id: id, state: 'password_not_set', label: 'Пароль не задан', description: '' });

describe('useOfferContractorLoginAccess', () => {
  beforeEach(() => getAccess.mockReset());
  it('checks visible contractors once even when they have multiple offers', async () => {
    getAccess.mockResolvedValue([access('one')]);
    const { result } = renderHook(() => useOfferContractorLoginAccess([offer('one'), offer('one'), offer('hidden', false)]));
    await waitFor(() => expect(result.current.states.get('one')?.state).toBe('password_not_set'));
    expect(getAccess).toHaveBeenCalledOnce();
    expect(getAccess.mock.calls[0][0]).toEqual(['one']);
  });
  it('does not fetch without an allowed contractor info action', () => {
    renderHook(() => useOfferContractorLoginAccess([offer('hidden', false)]));
    expect(getAccess).not.toHaveBeenCalled();
  });
  it('reports unknown after a failed check and can refresh successfully', async () => {
    getAccess.mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce([access('one')]);
    const { result } = renderHook(() => useOfferContractorLoginAccess([offer('one')]));
    await waitFor(() => expect(result.current.states.get('one')?.state).toBe('unknown'));
    act(() => result.current.refresh());
    await waitFor(() => expect(result.current.states.get('one')?.state).toBe('password_not_set'));
  });
  it('aborts old requests and ignores their response after switching contractors', async () => {
    let resolveFirst!: (items: ContractorLoginAccess[]) => void;
    getAccess.mockReturnValueOnce(new Promise<ContractorLoginAccess[]>((resolve) => { resolveFirst = resolve; }))
      .mockResolvedValueOnce([access('two')]);
    const { result, rerender } = renderHook(({ id }) => useOfferContractorLoginAccess([offer(id)]), { initialProps: { id: 'one' } });
    const firstSignal = getAccess.mock.calls[0][1] as AbortSignal;
    rerender({ id: 'two' });
    expect(firstSignal.aborted).toBe(true);
    await waitFor(() => expect(result.current.states.has('two')).toBe(true));
    await act(async () => resolveFirst([access('one')]));
    expect(result.current.states.has('one')).toBe(false);
    expect(result.current.states.has('two')).toBe(true);
  });
});
