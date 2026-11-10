import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fetchJson } from '../client';
import { getManualContractorDuplicates } from './getManualContractorDuplicates';

vi.mock('../client', () => ({ fetchJson: vi.fn() }));

describe('getManualContractorDuplicates', () => {
  beforeEach(() => vi.mocked(fetchJson).mockReset());

  it('uses the request endpoint and retains the server reason for a disabled duplicate', async () => {
    const reason = 'Данный контрагент уже приложил КП к текущей заявке';
    vi.mocked(fetchJson).mockResolvedValue({ data: { items: [{
      user_id: 'beton', inn: '7707083893', status: 'active', can_select: false, disabled_reason: reason,
    }] } });

    const [item] = await getManualContractorDuplicates({ requestId: 'заявка/1', inn: ' 7707083893 ' });

    expect(fetchJson).toHaveBeenCalledWith(
      `/api/v1/requests/${encodeURIComponent('заявка/1')}/offers/manual/contractor-duplicates?inn=7707083893`,
      {}, 'Не удалось проверить похожих контрагентов'
    );
    expect(item).toEqual(expect.objectContaining({ userId: 'beton', inn: '7707083893', canSelect: false, disabledReason: reason }));
  });

  it('keeps directory lookup separate and never enables an absent action flag', async () => {
    vi.mocked(fetchJson).mockResolvedValue({ data: { items: [{ user_id: 'beton', status: 'active' }] } });

    const [item] = await getManualContractorDuplicates({});

    expect(fetchJson).toHaveBeenCalledWith('/api/v1/users/manual-contractor-duplicates', {}, 'Не удалось проверить похожих контрагентов');
    expect(item.canSelect).toBe(false);
  });
});
