import { describe, expect, it, vi } from 'vitest';
import { fetchJson } from '../client';
import { getContractorLoginAccess } from './getContractorLoginAccess';
vi.mock('../client', () => ({ fetchJson: vi.fn().mockResolvedValue({ data: { items: [] } }) }));

describe('getContractorLoginAccess', () => {
  it('deduplicates and splits batches with abort and no-store options', async () => {
    const signal = new AbortController().signal;
    const ids = Array.from({ length: 101 }, (_, index) => `contractor-${index}`);
    await getContractorLoginAccess([...ids, ids[0]], signal);
    expect(fetchJson).toHaveBeenCalledTimes(2);
    const first = vi.mocked(fetchJson).mock.calls[0];
    const second = vi.mocked(fetchJson).mock.calls[1];
    expect(new URL(first[0], 'http://test').searchParams.getAll('contractor_id')).toHaveLength(100);
    expect(new URL(second[0], 'http://test').searchParams.getAll('contractor_id')).toEqual(['contractor-100']);
    expect(first[1]).toEqual({ method: 'GET', signal, cache: 'no-store' });
  });
});
