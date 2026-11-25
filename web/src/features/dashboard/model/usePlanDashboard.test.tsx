import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { closePlan, deletePlan, getPlanDashboard } from '@shared/api/plans';
import { usePlanDashboard } from './usePlanDashboard';

vi.mock('@shared/api/plans', () => ({
  getPlanDashboard: vi.fn(), deletePlan: vi.fn(), closePlan: vi.fn(),
  createRootPlan: vi.fn(), createSubplan: vi.fn(), delegatePlan: vi.fn(),
  getPlanDelegateCandidates: vi.fn(), updatePlan: vi.fn(),
}));
const toasts = vi.hoisted(() => ({ showErrorToast: vi.fn(), showSuccessToast: vi.fn() }));
vi.mock('@shared/ui/toasts', () => ({ useSystemToasts: () => toasts }));

describe('plan confirmation mutation results', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.mocked(getPlanDashboard).mockResolvedValue({} as never);
  });

  it.each(['removeChildPlan', 'closePlanNode'] as const)('returns failure for %s so the confirmation can stay open and retry', async (action) => {
    const api = vi.mocked(action === 'removeChildPlan' ? deletePlan : closePlan);
    api.mockRejectedValueOnce(new Error('Операция с планом не выполнена')).mockResolvedValueOnce(undefined as never);
    const { result } = renderHook(usePlanDashboard);
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    let success: boolean | undefined;
    await act(async () => { success = await result.current[action](9); });
    expect(success).toBe(false);
    expect(result.current.isMutating).toBe(false);
    expect(toasts.showErrorToast).toHaveBeenCalledOnce();
    await act(async () => { success = await result.current[action](9); });
    expect(success).toBe(true);
    expect(api).toHaveBeenCalledTimes(2);
    expect(result.current.errorMessage).toBeNull();
  });
});
