import { describe, expect, it } from 'vitest';
import { ROLE } from '@shared/constants/roles';
import { buildPeopleTree } from './buildPeopleTree';

describe('buildPeopleTree', () => {
  it('sorts business roles before administration without deriving reporting links', () => {
    const tree = buildPeopleTree([
      { user_id: 'admin', full_name: 'Администратор', role_id: ROLE.ADMIN },
      { user_id: 'superadmin', full_name: 'Суперадминистратор', role_id: ROLE.SUPERADMIN },
      { user_id: 'pm', full_name: 'РП', role_id: ROLE.PROJECT_MANAGER },
    ].map((member) => ({ ...member, role_name: '', status: 'active', id_parent_user: null })));

    expect(tree.map((node) => node.user_id)).toEqual(['pm', 'admin', 'superadmin']);
    expect(tree.every((node) => node.children.length === 0)).toBe(true);
  });
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
