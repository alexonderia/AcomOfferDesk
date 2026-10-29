import { describe, expect, it } from 'vitest';
import { ROLE } from '@shared/constants/roles';
import { roleGuides } from './roleGuides';

const hierarchyRoles = [
  ROLE.OPERATOR,
  ROLE.ECONOMIST,
  ROLE.LEAD_ECONOMIST,
  ROLE.PROJECT_MANAGER,
  ROLE.ADMIN,
  ROLE.SUPERADMIN
];

describe('roleGuides hierarchy section', () => {
  it.each(hierarchyRoles)('includes hierarchy block for role %s', (roleId) => {
    const guide = roleGuides[roleId];
    expect(guide).toBeDefined();
    expect(guide.sections[0]?.title).toBe('Перед началом работы: иерархия');
  });

  it('keeps contractor memo without hierarchy block', () => {
    expect(roleGuides[ROLE.CONTRACTOR].sections[0]?.title).not.toBe(
      'Перед началом работы: иерархия'
    );
  });
});
