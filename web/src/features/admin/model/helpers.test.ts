import { describe, expect, it } from 'vitest';
import { ROLE } from '@shared/constants/roles';
import { getScopedCreateRoleIds } from './helpers';

describe('getScopedCreateRoleIds', () => {
  it('removes contractor from employee creation tabs', () => {
    const roleIds = getScopedCreateRoleIds({
      activeTab: 'economists',
      availableRoleIds: [ROLE.ECONOMIST, ROLE.OPERATOR, ROLE.CONTRACTOR],
      sessionRoleId: ROLE.ADMIN
    });

    expect(roleIds).toEqual([ROLE.ECONOMIST, ROLE.OPERATOR]);
  });

  it('keeps only contractor on the contractor tab for non-superadmin users', () => {
    const roleIds = getScopedCreateRoleIds({
      activeTab: 'contractors',
      availableRoleIds: [ROLE.ADMIN, ROLE.CONTRACTOR, ROLE.ECONOMIST],
      sessionRoleId: ROLE.ADMIN
    });

    expect(roleIds).toEqual([ROLE.CONTRACTOR]);
  });

  it('moves contractor first on the contractor tab for superadmin and keeps other roles after it', () => {
    const roleIds = getScopedCreateRoleIds({
      activeTab: 'contractors',
      availableRoleIds: [ROLE.ADMIN, ROLE.CONTRACTOR, ROLE.ECONOMIST],
      sessionRoleId: ROLE.SUPERADMIN
    });

    expect(roleIds).toEqual([ROLE.CONTRACTOR, ROLE.ADMIN, ROLE.ECONOMIST]);
  });

  it('moves the current superadmin page role to the first position', () => {
    const roleIds = getScopedCreateRoleIds({
      activeTab: 'lead_economists',
      availableRoleIds: [ROLE.ADMIN, ROLE.PROJECT_MANAGER, ROLE.LEAD_ECONOMIST, ROLE.ECONOMIST, ROLE.OPERATOR],
      sessionRoleId: ROLE.SUPERADMIN
    });

    expect(roleIds).toEqual([
      ROLE.LEAD_ECONOMIST,
      ROLE.ADMIN,
      ROLE.PROJECT_MANAGER,
      ROLE.ECONOMIST,
      ROLE.OPERATOR
    ]);
  });

  it('preserves the original order when the current page role is unavailable', () => {
    const roleIds = getScopedCreateRoleIds({
      activeTab: 'admins',
      availableRoleIds: [ROLE.ECONOMIST, ROLE.OPERATOR],
      sessionRoleId: ROLE.SUPERADMIN
    });

    expect(roleIds).toEqual([ROLE.ECONOMIST, ROLE.OPERATOR]);
  });

  it('moves security officer first on the dedicated tab for superadmin', () => {
    const roleIds = getScopedCreateRoleIds({
      activeTab: 'security_officers',
      availableRoleIds: [ROLE.ADMIN, ROLE.SECURITY_OFFICER, ROLE.ECONOMIST],
      sessionRoleId: ROLE.SUPERADMIN
    });

    expect(roleIds).toEqual([ROLE.SECURITY_OFFICER, ROLE.ADMIN, ROLE.ECONOMIST]);
  });
});
