import { act, cleanup, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { getSystemStatus } from '@shared/api/system/getSystemStatus';
import { systemStatusFixture } from './systemStatus.fixture';
import { useSystemStatus } from './useSystemStatus';

vi.mock('@shared/api/system/getSystemStatus', () => ({ getSystemStatus: vi.fn() }));
const fetchStatus = vi.mocked(getSystemStatus);

describe('system status refresh', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    fetchStatus.mockReset();
    fetchStatus.mockResolvedValue(systemStatusFixture);
    Object.defineProperty(document, 'hidden', { configurable: true, value: false });
  });
  afterEach(() => { cleanup(); vi.useRealTimers(); });

  it('loads and polls visible pages, refreshes manually', async () => {
    const { result } = renderHook(useSystemStatus);
    await act(async () => {});
    expect(result.current.data).toBe(systemStatusFixture);
    expect(result.current.loading).toBe(false);
    await act(async () => { vi.advanceTimersByTime(30_000); });
    expect(fetchStatus).toHaveBeenCalledTimes(2);
    await act(async () => result.current.reload());
    expect(fetchStatus).toHaveBeenCalledTimes(3);
  });

  it('keeps last result with an explicit error and recovers', async () => {
    const { result } = renderHook(useSystemStatus);
    await act(async () => {});
    fetchStatus.mockRejectedValueOnce(new Error('Сервис недоступен'));
    await act(async () => result.current.reload());
    expect(result.current.data).toBe(systemStatusFixture);
    expect(result.current.error).toBe('Сервис недоступен');
    await act(async () => result.current.reload());
    expect(result.current.error).toBeNull();
  });

  it('pauses hidden-page polling and refreshes when page becomes visible', async () => {
    renderHook(useSystemStatus);
    await act(async () => {});
    Object.defineProperty(document, 'hidden', { configurable: true, value: true });
    await act(async () => { vi.advanceTimersByTime(60_000); });
    expect(fetchStatus).toHaveBeenCalledTimes(1);
    Object.defineProperty(document, 'hidden', { configurable: true, value: false });
    await act(async () => document.dispatchEvent(new Event('visibilitychange')));
    expect(fetchStatus).toHaveBeenCalledTimes(2);
  });

  it('prevents overlapping polling and aborts on unmount', async () => {
    fetchStatus.mockImplementation(() => new Promise(() => {}));
    const { unmount } = renderHook(useSystemStatus);
    const signal = fetchStatus.mock.calls[0][0];
    await act(async () => { vi.advanceTimersByTime(90_000); });
    expect(fetchStatus).toHaveBeenCalledTimes(1);
    unmount();
    expect(signal?.aborted).toBe(true);
    await act(async () => { vi.advanceTimersByTime(30_000); document.dispatchEvent(new Event('visibilitychange')); });
    expect(fetchStatus).toHaveBeenCalledTimes(1);
  });
});
