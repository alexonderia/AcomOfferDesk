import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fetchJson } from '../client';
import { getRequestContractors } from './getRequestContractors';

vi.mock('../client', () => ({ fetchJson: vi.fn() }));

describe('getRequestContractors selection state', () => {
  beforeEach(() => vi.clearAllMocks());

  it('preserves the server selection state for this request and denies absent flags', async () => {
    const reason = 'Данный контрагент уже приложил КП к текущей заявке';
    vi.mocked(fetchJson).mockResolvedValue({ data: { items: [
      { user_id: 'available', can_select: true },
      { user_id: 'existing', can_select: false, disabled_reason: reason },
      { user_id: 'without-flag' },
    ] } });

    const { items } = await getRequestContractors('заявка/1');

    expect(fetchJson).toHaveBeenCalledWith(
      `/api/v1/requests/${encodeURIComponent('заявка/1')}/offers/manual/eligible-contractors`,
      { method: 'GET' }, 'Ошибка загрузки контрагентов'
    );
    expect(items.map(({ can_select, disabled_reason }) => ({ can_select, disabled_reason }))).toEqual([
      { can_select: true, disabled_reason: null },
      { can_select: false, disabled_reason: reason },
      { can_select: false, disabled_reason: null },
    ]);
  });

  it('keeps loading the global contractor list for request creation', async () => {
    vi.mocked(fetchJson).mockResolvedValue({ data: { items: [{ user_id: 'contractor-1' }] } });

    const { items } = await getRequestContractors();

    expect(fetchJson).toHaveBeenCalledWith(
      '/api/v1/users/request-contractors', { method: 'GET' }, 'Ошибка загрузки контрагентов'
    );
    expect(items[0].user_id).toBe('contractor-1');
  });
});
