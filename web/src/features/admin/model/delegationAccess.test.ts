import { describe, expect, it } from 'vitest';

import {
  getIndividuallyGrantedAccessCodes,
  permissionSourceLabel,
  withIndividualGrant,
} from './delegationAccess';

describe('delegation access source state', () => {
  it('distinguishes role, individual, combined, and absent sources', () => {
    expect(permissionSourceLabel(true, false)).toBe('Через роль');
    expect(permissionSourceLabel(false, true)).toBe('Индивидуально');
    expect(permissionSourceLabel(true, true)).toBe('Через роль + индивидуально');
    expect(permissionSourceLabel(false, false)).toBe('Отсутствует');
  });

  it('removes only the individual grant while preserving effective role access', () => {
    const access = withIndividualGrant(
      {
        code: 'delegation.department.requests.read',
        enabled: true,
        grantedViaRole: true,
        grantedIndividually: true,
      },
      false
    );

    expect(access.grantedIndividually).toBe(false);
    expect(access.enabled).toBe(true);
    expect(getIndividuallyGrantedAccessCodes([access])).toEqual([]);
  });

  it('submits only individually selected legacy access codes', () => {
    expect(getIndividuallyGrantedAccessCodes([
      {
        code: 'role-only',
        enabled: true,
        grantedViaRole: true,
        grantedIndividually: false,
      },
      {
        code: 'individual',
        enabled: true,
        grantedViaRole: false,
        grantedIndividually: true,
      },
    ])).toEqual(['individual']);
  });
});
