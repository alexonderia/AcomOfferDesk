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
