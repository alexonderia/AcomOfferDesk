import { describe, expect, it } from 'vitest';
import { ROLE } from '@shared/constants/roles';
import { buildPeopleTree } from './buildPeopleTree';

describe('buildPeopleTree', () => {
  it('keeps same-unit members as peer roots and ignores legacy member parent links', () => {
    const tree = buildPeopleTree([
      {
        user_id: 'lead',
        full_name: 'Lead',
        role_id: ROLE.PROJECT_MANAGER,
        role_name: 'Руководитель проекта',
        status: 'active',
        id_parent_user: null,
      },
      {
        user_id: 'economist',
        full_name: 'Economist',
        role_id: ROLE.ECONOMIST,
        role_name: 'Экономист',
        status: 'active',
        id_parent_user: 'lead',
      },
    ]);

    expect(tree.map((node) => node.user_id)).toEqual(['lead', 'economist']);
    expect(tree.every((node) => node.children.length === 0)).toBe(true);
  });
});
