import { describe, expect, it } from 'vitest';
import type { UnitNode } from '@shared/api/units';
import type { ResponsibilityEmployeeNode } from '@shared/api/users/getResponsibilityDashboard';
import { ROLE } from '@shared/constants/roles';
import {
  buildOrphanEmployeeRoots,
  buildUnitEmployeeRoots,
  indexEmployeeNodes,
} from './buildUnitWorkloadTree';

const makeEmployee = (
  userId: string,
  parentUserId: string | null = null,
  children: ResponsibilityEmployeeNode[] = [],
): ResponsibilityEmployeeNode => ({
  user_id: userId,
  full_name: userId,
  role_id: ROLE.ECONOMIST,
  role_name: 'Экономист',
  parent_user_id: parentUserId,
  in_progress_total: 1,
  statuses: [],
  children,
});

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

describe('buildUnitWorkloadTree', () => {
  it('builds one employee tree from the whole unit subtree', () => {
    const rootUnit = makeUnit(1, [
      {
        user_id: 'lead',
        full_name: 'Lead',
        role_id: ROLE.PROJECT_MANAGER,
        role_name: 'Руководитель',
        status: 'active',
        id_parent_user: null,
      },
    ], [
      makeUnit(2, [
        {
          user_id: 'economist',
          full_name: 'Economist',
          role_id: ROLE.ECONOMIST,
          role_name: 'Экономист',
          status: 'active',
          id_parent_user: 'lead',
        },
      ]),
    ]);

    const tree = [
      makeEmployee('lead', null, [makeEmployee('economist', 'lead')]),
    ];
    const employeeById = indexEmployeeNodes(tree);

    const rootEmployees = buildUnitEmployeeRoots(rootUnit, employeeById);
    expect(rootEmployees.map((node) => node.user_id)).toEqual(['lead']);
    expect(rootEmployees[0]?.children.map((node) => node.user_id)).toEqual(['economist']);
  });

  it('keeps child unit employees under the parent unit branch even without employee parent links', () => {
    const rootUnit = makeUnit(1, [
      {
        user_id: 'lead',
        full_name: 'Lead',
        role_id: ROLE.PROJECT_MANAGER,
        role_name: 'Руководитель',
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
    ]);

    const tree = [
      makeEmployee('lead'),
      makeEmployee('senior'),
      makeEmployee('staff'),
    ];
    const employeeById = indexEmployeeNodes(tree);

    const rootEmployees = buildUnitEmployeeRoots(rootUnit, employeeById);

    expect(rootEmployees.map((node) => node.user_id)).toEqual(['lead']);
    expect(rootEmployees[0]?.children.map((node) => node.user_id)).toEqual(['senior']);
    expect(rootEmployees[0]?.children[0]?.children.map((node) => node.user_id)).toEqual(['staff']);
  });

  it('keeps sibling unit branches separate when the parent unit has no direct staff', () => {
    const rootUnit = makeUnit(1, [], [
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
    ]);

    const tree = [
      makeEmployee('olga'),
      makeEmployee('ivan'),
      makeEmployee('gd'),
      makeEmployee('pp'),
    ];
    const employeeById = indexEmployeeNodes(tree);

    const rootEmployees = buildUnitEmployeeRoots(rootUnit, employeeById);

    expect(rootEmployees.map((node) => node.user_id)).toEqual(['olga', 'gd']);
    expect(rootEmployees[0]?.children.map((node) => node.user_id)).toEqual(['ivan']);
    expect(rootEmployees[1]?.children.map((node) => node.user_id)).toEqual(['pp']);
  });

  it('returns employees without units as orphan roots', () => {
    const tree = [makeEmployee('solo')];
    const orphans = buildOrphanEmployeeRoots(tree, new Set(['other-user']));

    expect(orphans.map((node) => node.user_id)).toEqual(['solo']);
  });
});
