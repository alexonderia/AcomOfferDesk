import { describe, expect, it } from 'vitest';
import type { UnitNode } from '@shared/api/units';
import { ROLE } from '@shared/constants/roles';
import { buildUnitPeopleTree } from './buildUnitPeopleTree';

const makeUnit = (
  unitId: number,
  members: UnitNode['members'],
  children: UnitNode[] = [],
): UnitNode => ({
  unit_id: unitId,
  name: `Unit ${unitId}`,
  id_parent: null,
  is_active: true,
  members,
  children,
  actions: {
    canCreateChild: false,
    canUpdate: false,
    canDelete: false,
    canManageMembers: false,
  },
});

describe('buildUnitPeopleTree', () => {
  const member = (userId: string, roleId: number): UnitNode['members'][number] => ({
    user_id: userId, full_name: userId, role_id: roleId, role_name: String(roleId), status: 'active', id_parent_user: null,
  });

  it('puts the project manager above child business units while keeping an administrator separate', () => {
    const tree = buildUnitPeopleTree(makeUnit(1, [
      member('administrator', ROLE.ADMIN), member('project-manager', ROLE.PROJECT_MANAGER),
    ], [makeUnit(2, [member('lead', ROLE.LEAD_ECONOMIST)], [makeUnit(3, [member('economist', ROLE.ECONOMIST)])])]));

    expect(tree.map((node) => node.user_id)).toEqual(['project-manager', 'administrator']);
    expect(tree[0].children.map((node) => node.user_id)).toEqual(['lead']);
    expect(tree[0].children[0].children.map((node) => node.user_id)).toEqual(['economist']);
    expect(tree[1].children).toEqual([]);
  });

  it.each([ROLE.ADMIN, ROLE.SUPERADMIN, ROLE.SECURITY_OFFICER, ROLE.OPERATOR])('does not invent business subordinates for parent role %s', (roleId) => {
    const tree = buildUnitPeopleTree(makeUnit(1, [member('parent', roleId)], [
      makeUnit(2, [member('staff', ROLE.ECONOMIST)]),
    ]));

    expect(tree.map((node) => node.user_id).sort()).toEqual(['parent', 'staff']);
    expect(tree.every((node) => node.children.length === 0)).toBe(true);
  });

  it('does not put administrative roles from descendant units under the business manager', () => {
    const tree = buildUnitPeopleTree(makeUnit(1, [member('project-manager', ROLE.PROJECT_MANAGER)], [
      makeUnit(2, [member('administrator', ROLE.ADMIN), member('lead', ROLE.LEAD_ECONOMIST)], [
        makeUnit(3, [member('superadmin', ROLE.SUPERADMIN), member('economist', ROLE.ECONOMIST)]),
      ]),
    ]));

    expect(tree.map((node) => node.user_id)).toEqual(['project-manager', 'administrator', 'superadmin']);
    expect(tree[0].children.map((node) => node.user_id)).toEqual(['lead']);
    expect(tree[0].children[0].children.map((node) => node.user_id)).toEqual(['economist']);
    expect(tree.slice(1).every((node) => node.children.length === 0)).toBe(true);
  });

  it('keeps child unit staff nested by unit structure when member parent links are missing', () => {
    const tree = buildUnitPeopleTree(
      makeUnit(1, [
        {
          user_id: 'lead',
          full_name: 'Lead',
          role_id: ROLE.PROJECT_MANAGER,
          role_name: 'Руководитель проекта',
          status: 'active',
          id_parent_user: null,
        },
      ], [
        makeUnit(2, [
          {
            user_id: 'senior',
            full_name: 'Senior',
            role_id: ROLE.LEAD_ECONOMIST,
            role_name: 'Ведущий экономист',
            status: 'active',
            id_parent_user: null,
          },
        ], [
          makeUnit(3, [
            {
              user_id: 'staff',
              full_name: 'Staff',
              role_id: ROLE.ECONOMIST,
              role_name: 'Экономист',
              status: 'active',
              id_parent_user: null,
            },
          ]),
        ]),
      ]),
    );

    expect(tree.map((node) => node.user_id)).toEqual(['lead']);
    expect(tree[0]?.children.map((node) => node.user_id)).toEqual(['senior']);
    expect(tree[0]?.children[0]?.children.map((node) => node.user_id)).toEqual(['staff']);
  });

  it('ignores legacy member parent links when sibling unit branches are built', () => {
    const tree = buildUnitPeopleTree(
      makeUnit(1, [], [
        makeUnit(2, [
          {
            user_id: 'olga',
            full_name: 'Olga',
            role_id: ROLE.LEAD_ECONOMIST,
            role_name: 'Ведущий экономист',
            status: 'active',
            id_parent_user: null,
          },
        ]),
        makeUnit(3, [
          {
            user_id: 'gd',
            full_name: 'GD',
            role_id: ROLE.LEAD_ECONOMIST,
            role_name: 'Ведущий экономист',
            status: 'active',
            id_parent_user: 'olga',
          },
        ]),
      ]),
    );

    expect(tree.map((node) => node.user_id)).toEqual(['olga', 'gd']);
  });

  it('keeps sibling child unit branches separate when the parent unit has no staff', () => {
    const tree = buildUnitPeopleTree(
      makeUnit(1, [], [
        makeUnit(2, [
          {
            user_id: 'olga',
            full_name: 'Olga',
            role_id: ROLE.LEAD_ECONOMIST,
            role_name: 'Ведущий экономист',
            status: 'active',
            id_parent_user: null,
          },
        ], [
          makeUnit(3, [
            {
              user_id: 'ivan',
              full_name: 'Ivan',
              role_id: ROLE.ECONOMIST,
              role_name: 'Экономист',
              status: 'active',
              id_parent_user: null,
            },
          ]),
        ]),
        makeUnit(4, [
          {
            user_id: 'gd',
            full_name: 'GD',
            role_id: ROLE.LEAD_ECONOMIST,
            role_name: 'Ведущий экономист',
            status: 'active',
            id_parent_user: null,
          },
        ], [
          makeUnit(5, [
            {
              user_id: 'pp',
              full_name: 'PP',
              role_id: ROLE.ECONOMIST,
              role_name: 'Экономист',
              status: 'active',
              id_parent_user: null,
            },
          ]),
        ]),
      ]),
    );

    expect(tree.map((node) => node.user_id)).toEqual(['olga', 'gd']);
    expect(tree[0]?.children.map((node) => node.user_id)).toEqual(['ivan']);
    expect(tree[1]?.children.map((node) => node.user_id)).toEqual(['pp']);
  });

  it('does not duplicate a parent-unit member when the same user exists in a child unit', () => {
    const tree = buildUnitPeopleTree(
      makeUnit(1, [
        {
          user_id: 'lead',
          full_name: 'Lead',
          role_id: ROLE.PROJECT_MANAGER,
          role_name: 'Руководитель проекта',
          status: 'active',
          id_parent_user: null,
        },
        {
          user_id: 'shared',
          full_name: 'Shared',
          role_id: ROLE.LEAD_ECONOMIST,
          role_name: 'Ведущий экономист',
          status: 'active',
          id_parent_user: null,
        },
      ], [
        makeUnit(2, [
          {
            user_id: 'shared',
            full_name: 'Shared',
            role_id: ROLE.LEAD_ECONOMIST,
            role_name: 'Ведущий экономист',
            status: 'active',
            id_parent_user: null,
          },
        ]),
      ]),
    );

    expect(tree.map((node) => node.user_id)).toEqual(['lead']);
    expect(tree[0]?.children.map((node) => node.user_id)).toEqual(['shared']);
  });
});
