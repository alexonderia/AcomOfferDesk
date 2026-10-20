import { describe, expect, it } from 'vitest';
import type { UnitNode } from '@shared/api/units';
import type { UserHierarchy } from '@shared/api/users/getUserHierarchy';
import { buildUnitRelationKinds, buildUserHierarchyDisplayUnits, collectUniqueStaff } from './userHierarchyTreeUtils';
import { buildUnitPeopleTree } from '@shared/lib/hierarchy/buildUnitPeopleTree';

const makeUnit = (
  unitId: number,
  name: string,
  members: UnitNode['members'] = [],
  children: UnitNode[] = [],
  idParent: number | null = null,
): UnitNode => ({
  unit_id: unitId,
  name,
  id_parent: idParent,
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

const baseHierarchy: UserHierarchy = {
  user: {
    userId: 'pp',
    fullName: 'ппп ппп рр',
    roleId: 6,
    roleName: 'Экономист',
    status: 'active',
  },
  units: [],
  managers: [
    {
      userId: 'olga',
      fullName: 'Иванова Ольга Игоревна',
      roleId: 5,
      roleName: 'Ведущий экономист',
      status: 'active',
      sourceUnitId: 21,
      sourceUnitName: 'Модуль 2.1',
    },
    {
      userId: 'gd',
      fullName: 'gsgsg dgdg кн5ун',
      roleId: 5,
      roleName: 'Ведущий экономист',
      status: 'active',
      sourceUnitId: 22,
      sourceUnitName: 'Модуль 2.2',
    },
    {
      userId: 'ivan',
      fullName: 'Иванов Иван Иванович',
      roleId: 6,
      roleName: 'Экономист',
      status: 'active',
      sourceUnitId: 211,
      sourceUnitName: 'Модуль 2.1.1',
    },
  ],
  subordinates: [],
  legacyHierarchy: {
    legacyManager: null,
    legacySubordinates: [],
    isBusinessSource: false,
    note: '',
  },
};

describe('userHierarchyTreeUtils', () => {
  it('shows child units of the department with the full module subtree', () => {
    const unitsTree = [
      makeUnit(1, 'АО', [
        {
          user_id: 'root-pm',
          full_name: 'пп ии ыкаыка',
          role_id: 4,
          role_name: 'Руководитель Проекта',
          status: 'active',
          id_parent_user: null,
        },
      ], [
        makeUnit(2, 'Модуль 2', [], [
          makeUnit(21, 'Модуль 2.1', [
            {
              user_id: 'olga',
              full_name: 'Иванова Ольга Игоревна',
              role_id: 5,
              role_name: 'Ведущий экономист',
              status: 'active',
              id_parent_user: null,
            },
          ], [
            makeUnit(211, 'Модуль 2.1.1', [
              {
                user_id: 'ivan',
                full_name: 'Иванов Иван Иванович',
                role_id: 6,
                role_name: 'Экономист',
                status: 'active',
                id_parent_user: null,
              },
            ], [], 21),
          ], 2),
          makeUnit(22, 'Модуль 2.2', [
            {
              user_id: 'gd',
              full_name: 'gsgsg dgdg кн5ун',
              role_id: 5,
              role_name: 'Ведущий экономист',
              status: 'active',
              id_parent_user: null,
            },
          ], [
            makeUnit(221, 'Модуль 2.2.1', [
              {
                user_id: 'pp',
                full_name: 'ппп ппп рр',
                role_id: 6,
                role_name: 'Экономист',
                status: 'active',
                id_parent_user: null,
              },
            ], [], 22),
          ], 2),
        ], 1),
      ]),
    ];

    const displayUnits = buildUserHierarchyDisplayUnits(baseHierarchy, unitsTree);

    expect(displayUnits).toHaveLength(1);
    expect(displayUnits[0]?.departmentName).toBe('АО');
    expect(displayUnits[0]?.unit.name).toBe('Модуль 2');
    expect(collectUniqueStaff(displayUnits[0]!.unit).map((member) => member.user_id).sort()).toEqual([
      'gd',
      'ivan',
      'olga',
      'pp',
    ]);
  });

  it('shows one module card per department where the selected user is assigned', () => {
    const unitsTree = [
      makeUnit(1, 'УЭ', [], [
        makeUnit(10, 'Модуль 1', [
          {
            user_id: 'pp',
            full_name: 'ппп ппп рр',
            role_id: 6,
            role_name: 'Экономист',
            status: 'active',
            id_parent_user: null,
          },
        ], [
          makeUnit(101, 'Модуль 1.1', [
            {
              user_id: 'ue-lead',
              full_name: 'Ведущий УЭ',
              role_id: 5,
              role_name: 'Ведущий экономист',
              status: 'active',
              id_parent_user: null,
            },
          ], [], 10),
          makeUnit(102, 'Модуль 1.2', [
            {
              user_id: 'ue-staff',
              full_name: 'Экономист УЭ',
              role_id: 6,
              role_name: 'Экономист',
              status: 'active',
              id_parent_user: null,
            },
          ], [], 10),
        ], 1),
      ]),
      makeUnit(2, 'АО', [], [
        makeUnit(20, 'Модуль 2', [], [
          makeUnit(21, 'Модуль 2.1', [
            {
              user_id: 'olga',
              full_name: 'Иванова Ольга Игоревна',
              role_id: 5,
              role_name: 'Ведущий экономист',
              status: 'active',
              id_parent_user: null,
            },
          ], [
            makeUnit(211, 'Модуль 2.1.1', [
              {
                user_id: 'ivan',
                full_name: 'Иванов Иван Иванович',
                role_id: 6,
                role_name: 'Экономист',
                status: 'active',
                id_parent_user: null,
              },
            ], [], 21),
          ], 20),
          makeUnit(22, 'Модуль 2.2', [
            {
              user_id: 'gd',
              full_name: 'gsgsg dgdg кн5ун',
              role_id: 5,
              role_name: 'Ведущий экономист',
              status: 'active',
              id_parent_user: null,
            },
          ], [
            makeUnit(221, 'Модуль 2.2.1', [
              {
                user_id: 'pp',
                full_name: 'ппп ппп рр',
                role_id: 6,
                role_name: 'Экономист',
                status: 'active',
                id_parent_user: null,
              },
            ], [], 22),
          ], 20),
        ], 2),
      ]),
    ];

    const displayUnits = buildUserHierarchyDisplayUnits(baseHierarchy, unitsTree);

    expect(displayUnits.map((item) => `${item.departmentName}/${item.unit.name}`)).toEqual([
      'УЭ/Модуль 1',
      'АО/Модуль 2',
    ]);
    expect(collectUniqueStaff(displayUnits[0]!.unit).map((member) => member.user_id).sort()).toEqual([
      'pp',
      'ue-lead',
      'ue-staff',
    ]);
  });

  it('does not mark a sibling root as subordinate when the selected employee is in another branch of the same unit tree', () => {
    const unitsTree = [
      makeUnit(2, 'Модуль 2', [], [
        makeUnit(21, 'Модуль 2.1', [
          {
            user_id: 'olga',
            full_name: 'Иванова Ольга Игоревна',
            role_id: 5,
            role_name: 'Ведущий экономист',
            status: 'active',
            id_parent_user: null,
          },
        ], [
          makeUnit(211, 'Модуль 2.1.1', [
            {
              user_id: 'ivan',
              full_name: 'Иванов Иван Иванович',
              role_id: 6,
              role_name: 'Экономист',
              status: 'active',
              id_parent_user: null,
            },
          ], [], 21),
        ]),
        makeUnit(22, 'Модуль 2.2', [
          {
            user_id: 'pp',
            full_name: 'ппп ппп рр',
            role_id: 6,
            role_name: 'Экономист',
            status: 'active',
            id_parent_user: null,
          },
        ]),
      ]),
    ];

    const relationKinds = buildUnitRelationKinds({
      roots: buildUnitPeopleTree(unitsTree[0]),
      selectedUserId: 'olga',
    });

    expect(relationKinds.get('olga')).toBe('self');
    expect(relationKinds.get('ivan')).toBe('subordinate');
    expect(relationKinds.get('pp')).toBeUndefined();
  });
});
