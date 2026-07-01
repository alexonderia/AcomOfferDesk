import { describe, expect, it } from 'vitest';
import type { UnitNode } from '@shared/api/units';
import { buildUnitOptions } from './buildUnitOptions';

const makeUnit = (
  unitId: number,
  name: string,
  children: UnitNode[] = [],
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
    canManageMembers: false,
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
