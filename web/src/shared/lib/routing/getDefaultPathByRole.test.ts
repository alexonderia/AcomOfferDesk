import { describe, expect, it } from 'vitest';

import { ROLE } from '@shared/constants/roles';

import { getDefaultPathByRole } from './getDefaultPathByRole';
import { resolveAuthenticatedPath } from './resolveAuthenticatedPath';

describe('getDefaultPathByRole', () => {
  it('sends administrator with users.read to /admin', () => {
    expect(getDefaultPathByRole(ROLE.ADMIN, ['users.read', 'profile.manage_any'])).toBe('/admin');
  });

  it('does not send administrator without requests permissions to /requests', () => {
    expect(getDefaultPathByRole(ROLE.ADMIN, ['users.read'])).toBe('/admin');
    expect(getDefaultPathByRole(ROLE.ADMIN, [])).toBe('/account');
  });

  it('sends users with requests.read to /requests', () => {
    expect(getDefaultPathByRole(ROLE.OPERATOR, ['requests.read'])).toBe('/requests');
  });
});

describe('resolveAuthenticatedPath', () => {
  it('uses permissions for default path after login', () => {
    const session = { roleId: ROLE.ADMIN, permissions: ['users.read'] };
    expect(resolveAuthenticatedPath('/', session)).toBe('/admin');
  });

  it('honours explicit next path when provided', () => {
    const session = { roleId: ROLE.ADMIN, permissions: ['users.read'] };
    expect(resolveAuthenticatedPath('/feedback', session)).toBe('/feedback');
  });
});
