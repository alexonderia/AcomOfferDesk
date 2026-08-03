import type { UnitNode } from '@shared/api/units';
import { orgNodeLayout } from './unitHierarchyStyles';

export const measureUnitSubtreeWidth = (unit: UnitNode): number => {
  const { cardWidth, childGap } = orgNodeLayout;

  if (unit.children.length === 0) {
    return cardWidth;
  }

  if (unit.children.length === 1) {
    return Math.max(cardWidth, measureUnitSubtreeWidth(unit.children[0]!));
  }

  const childrenWidth = unit.children.reduce((total, child, index) => {
    const gap = index > 0 ? childGap : 0;
    return total + gap + measureUnitSubtreeWidth(child);
  }, 0);

  return Math.max(cardWidth, childrenWidth);
};

export type ChildrenRowLayout = {
  childCenters: number[];
  childWidths: number[];
  rowWidth: number;
};

export const buildChildrenRowLayout = (children: UnitNode[]): ChildrenRowLayout => {
  const childWidths = children.map(measureUnitSubtreeWidth);
  const rowWidth = childWidths.reduce((total, width, index) => {
    const gap = index > 0 ? orgNodeLayout.childGap : 0;
    return total + gap + width;
  }, 0);

  let offset = 0;
  const childCenters = childWidths.map((width, index) => {
    if (index > 0) {
      offset += orgNodeLayout.childGap;
    }
    const center = offset + width / 2;
    offset += width;
    return center;
  });

  return { childCenters, childWidths, rowWidth };
};
