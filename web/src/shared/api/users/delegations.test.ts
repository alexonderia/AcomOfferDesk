import { beforeEach, describe, expect, it, vi } from 'vitest';

const client = vi.hoisted(() => ({ fetchJson: vi.fn() }));

vi.mock('../client', () => client);

import {
  getDepartmentDelegations,
  updateDepartmentDelegations,
} from './getDepartmentDelegations';

describe('department delegations IAM source mapping', () => {
  beforeEach(() => {
    client.fetchJson.mockReset();
  });

  it('maps role and individual grant sources from the Acom response', async () => {
    client.fetchJson.mockResolvedValue({
      data: {
        user_id: 'user-1',
        role_id: 6,
        can_manage: true,
        accesses: [
          {
            code: 'delegation.department.requests.read',
            permission_code: 'department.requests.read',
            group: 'requests',
            label: 'Просмотр заявок подразделения',
            enabled: true,
            granted_via_role: true,
            granted_individually: false,
          },
        ],
      },
    });

    const result = await getDepartmentDelegations('user-1');

    expect(result.accesses[0]).toMatchObject({
      enabled: true,
      grantedViaRole: true,
      grantedIndividually: false,
    });
  });

  it('keeps the existing Acom PUT contract for selected legacy access codes', async () => {
    client.fetchJson.mockResolvedValue({
      data: {
        user_id: 'user-1',
        role_id: 6,
        can_manage: true,
        accesses: [],
      },
    });

    await updateDepartmentDelegations(
      'user-1',
      ['delegation.department.requests.update']
    );

    expect(client.fetchJson).toHaveBeenCalledWith(
      '/api/v1/users/user-1/delegations/department',
      {
        method: 'PUT',
        body: JSON.stringify({
          access_codes: ['delegation.department.requests.update'],
        }),
      },
      'Failed to update department delegations'
    );
  });
});
