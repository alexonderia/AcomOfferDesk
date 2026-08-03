import type { UnitNode } from '@shared/api/units';

export type UnitOption = {
  unitId: number;
  label: string;
};

export const buildUnitOptions = (
  nodes: UnitNode[],
  path: string[] = [],
): UnitOption[] =>
  nodes.flatMap((unit) => {
    const nextPath = [...path, unit.name];
    return [
      { unitId: unit.unit_id, label: nextPath.join(' / ') },
      ...buildUnitOptions(unit.children, nextPath),
    ];
  });

export const buildManageableUnitOptions = (
  nodes: UnitNode[],
  path: string[] = [],
  withinManageableSubtree = false,
): UnitOption[] =>
  nodes.flatMap((unit) => {
    const nextPath = [...path, unit.name];
    const isManageable = unit.actions.canManageMembers || withinManageableSubtree;
    const children = buildManageableUnitOptions(unit.children, nextPath, isManageable);
    const self = isManageable
      ? [{ unitId: unit.unit_id, label: nextPath.join(' / ') }]
      : [];
    return [...self, ...children];
  });
