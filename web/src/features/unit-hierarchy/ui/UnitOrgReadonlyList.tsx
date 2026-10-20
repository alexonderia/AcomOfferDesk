import type { ReactNode } from 'react';
import type { UnitNode } from '@shared/api/units';
import { buildUnitPeopleTree } from '@shared/lib/hierarchy/buildUnitPeopleTree';
import { HierarchyPeopleEmptyState, HierarchyPeopleViewTree } from './HierarchyPeopleViewTree';
import type { HierarchyPersonTone, HierarchyPersonVisual } from '@shared/ui/hierarchy/hierarchyPersonUtils';

const hasVisibleStaff = (unit: UnitNode): boolean => {
  return buildUnitPeopleTree(unit).length > 0;
};

export const UnitOrgReadonlyList = ({
  emptyLabel = 'Сотрудников пока нет.',
  highlightRoots = true,
  resolveHighlight,
  resolveTone,
  resolveTooltipTitle,
  units,
}: {
  emptyLabel?: string;
  highlightRoots?: boolean;
  resolveHighlight?: (person: HierarchyPersonVisual) => boolean;
  resolveTone?: (person: HierarchyPersonVisual) => HierarchyPersonTone;
  resolveTooltipTitle?: (person: HierarchyPersonVisual) => ReactNode;
  units: UnitNode[];
}) => {
  const visibleUnits = units.filter(hasVisibleStaff);

  if (visibleUnits.length === 0) {
    return <HierarchyPeopleEmptyState label={emptyLabel} />;
  }

  return (
    <>
      {visibleUnits.map((unit) => (
        <HierarchyPeopleViewTree
          key={unit.unit_id}
          highlightRoots={highlightRoots}
          members={[]}
          roots={buildUnitPeopleTree(unit)}
          resolveHighlight={resolveHighlight}
          resolveTone={resolveTone}
          resolveTooltipTitle={resolveTooltipTitle}
        />
      ))}
    </>
  );
};

export { HierarchyPeopleEmptyState };
