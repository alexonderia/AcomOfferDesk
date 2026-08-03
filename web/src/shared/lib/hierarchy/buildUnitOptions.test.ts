import { describe, expect, it } from 'vitest';
import type { UnitNode } from '@shared/api/units';
import { buildManageableUnitOptions, buildUnitOptions } from './buildUnitOptions';

const makeUnit = (
  unitId: number,
  name: string,
  children: UnitNode[] = [],
  canManageMembers = false,
): UnitNode => ({
  unit_id: unitId,
  name,
  id_parent: null,
  is_active: true,
  members: [],
  children,
  actions: {
    canCreateChild: false,
    canUpdate: false,
    canDelete: false,
    canManageMembers,
  },
});

describe('buildUnitOptions', () => {
  it('builds nested labels for the units tree', () => {
    expect(buildUnitOptions([
      makeUnit(1, 'АО', [
        makeUnit(2, 'Модуль 1'),
      ]),
    ])).toEqual([
      { unitId: 1, label: 'АО' },
      { unitId: 2, label: 'АО / Модуль 1' },
    ]);
  });
});

describe('buildManageableUnitOptions', () => {
  it('includes only nodes with canManageMembers and their descendants', () => {
    expect(buildManageableUnitOptions([
      makeUnit(1, 'АО', [
        makeUnit(2, 'Модуль 1', [makeUnit(3, 'Группа')], true),
      ]),
    ])).toEqual([
      { unitId: 2, label: 'АО / Модуль 1' },
      { unitId: 3, label: 'АО / Модуль 1 / Группа' },
    ]);
  });
});
