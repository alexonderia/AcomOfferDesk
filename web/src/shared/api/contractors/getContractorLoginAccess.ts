import { fetchJson } from '../client';

export type ContractorLoginAccess = {
  user_id: string;
  state: 'available' | 'not_granted' | 'blocked' | 'pending' | 'password_not_set' | 'setup_required' | 'temporarily_locked' | 'unknown';
  label: string;
  description: string;
};

export const getContractorLoginAccess = async (userIds: string[], signal?: AbortSignal): Promise<ContractorLoginAccess[]> => {
  const ids = [...new Set(userIds)];
  const items: ContractorLoginAccess[] = [];
  for (let start = 0; start < ids.length; start += 100) {
    const params = new URLSearchParams();
    ids.slice(start, start + 100).forEach((id) => params.append('contractor_id', id));
    const response = await fetchJson<{ data: { items: ContractorLoginAccess[] } }>(
      `/api/v1/contractors/login-access?${params}`, { method: 'GET', signal, cache: 'no-store' },
      'Не удалось проверить возможность входа контрагентов'
    );
    items.push(...response.data.items);
  }
  return items;
};
