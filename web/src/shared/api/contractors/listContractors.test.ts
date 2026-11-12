import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fetchJson } from '../client';
import { listContractors } from './listContractors';

vi.mock('../client', () => ({ fetchJson: vi.fn() }));

describe('listContractors', () => {
  beforeEach(() => vi.mocked(fetchJson).mockReset());

  it('loads every page so search can find contractors beyond the first page', async () => {
    vi.mocked(fetchJson)
      .mockResolvedValueOnce({ data: {
        items: Array.from({ length: 100 }, (_, index) => ({ user_id: `company-${index}`, role_id: 3, status: 'active' })),
        total: 101, limit: 100, offset: 0,
      } })
      .mockResolvedValueOnce({ data: {
        items: [{ user_id: 'last-company', role_id: 3, status: 'active', company_name: 'Последняя компания' }],
        total: 101, limit: 100, offset: 100,
      } });

    const items = await listContractors();
    expect(items).toHaveLength(101);
    expect(items[100].companyName).toBe('Последняя компания');
    expect(fetchJson).toHaveBeenNthCalledWith(2, '/api/v1/contractors?limit=100&offset=100', { method: 'GET' }, expect.any(String));
  });

  it('stops on an empty page if the list shrinks while loading', async () => {
    vi.mocked(fetchJson).mockResolvedValue({ data: { items: [], total: 100, limit: 100, offset: 0 } });
    await expect(listContractors()).resolves.toEqual([]);
    expect(fetchJson).toHaveBeenCalledTimes(1);
  });

  it('reports a later-page failure instead of returning incomplete search data', async () => {
    vi.mocked(fetchJson)
      .mockResolvedValueOnce({ data: { items: [{ user_id: 'company-1', role_id: 3, status: 'active' }], total: 2 } })
      .mockRejectedValueOnce(new Error('Не удалось загрузить контрагентов'));
    await expect(listContractors()).rejects.toThrow('Не удалось загрузить контрагентов');
  });
});
