import { describe, expect, it } from 'vitest';
import type { UnitNode } from '@shared/api/units';
import { orgNodeLayout } from './unitHierarchyStyles';
import { buildChildrenRowLayout, measureUnitSubtreeWidth } from './orgNodeLayoutUtils';

const makeUnit = (unitId: number, name: string, children: UnitNode[] = []): UnitNode => ({
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

describe('measureUnitSubtreeWidth', () => {
  it('uses card width for a leaf node', () => {
    expect(measureUnitSubtreeWidth(makeUnit(1, 'Leaf'))).toBe(orgNodeLayout.cardWidth);
  });

  it('expands width for siblings with nested children', () => {
    const tree = makeUnit(1, 'Root', [
      makeUnit(2, 'Left', [makeUnit(4, 'Left child')]),
      makeUnit(3, 'Right', [
        makeUnit(5, 'Right A'),
        makeUnit(6, 'Right B'),
      ]),
    ]);

    const rightBranchWidth = orgNodeLayout.cardWidth * 2 + orgNodeLayout.childGap;
    const rootWidth = Math.max(orgNodeLayout.cardWidth, orgNodeLayout.cardWidth + orgNodeLayout.childGap + rightBranchWidth);

    expect(measureUnitSubtreeWidth(tree.children[1]!)).toBe(rightBranchWidth);
    expect(measureUnitSubtreeWidth(tree)).toBe(rootWidth);
  });
});

describe('buildChildrenRowLayout', () => {
  it('places child centers according to subtree widths', () => {
    const children = [
      makeUnit(1, 'Narrow'),
      makeUnit(2, 'Wide', [makeUnit(3, 'A'), makeUnit(4, 'B')]),
    ];
    const wideWidth = orgNodeLayout.cardWidth * 2 + orgNodeLayout.childGap;

    const layout = buildChildrenRowLayout(children);

    expect(layout.childWidths).toEqual([orgNodeLayout.cardWidth, wideWidth]);
    expect(layout.rowWidth).toBe(orgNodeLayout.cardWidth + orgNodeLayout.childGap + wideWidth);
    expect(layout.childCenters[0]).toBe(orgNodeLayout.cardWidth / 2);
    expect(layout.childCenters[1]).toBe(orgNodeLayout.cardWidth + orgNodeLayout.childGap + wideWidth / 2);
  });
});
