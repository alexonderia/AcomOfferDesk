import type { UnitNode } from '@shared/api/units';
import { ROLE } from '@shared/constants/roles';
import { sortPersonTreeNodes, type PersonTreeNode } from './buildPeopleTree';

const collectDescendantUserIds = (units: UnitNode[], target: Set<string>) => {
  units.forEach((unit) => {
    unit.members.forEach((member) => {
      if (member.role_id !== ROLE.CONTRACTOR) {
        target.add(member.user_id);
      }
    });
    collectDescendantUserIds(unit.children, target);
  });
};

const attachChildRoots = (
  localRoots: PersonTreeNode[],
  roots: PersonTreeNode[],
  childRoots: PersonTreeNode[],
): PersonTreeNode[] => {
  if (childRoots.length === 0) {
    return roots;
  }

  const primaryRoot = localRoots[0] ?? null;

  if (!primaryRoot) {
    return [...roots, ...childRoots];
  }

  primaryRoot.children.push(...childRoots);
  sortPersonTreeNodes(primaryRoot.children);
  return roots;
};

export const buildUnitPeopleTree = (unit: UnitNode): PersonTreeNode[] => {
  const descendantUserIds = new Set<string>();
  collectDescendantUserIds(unit.children, descendantUserIds);
  const localStaff = unit.members.filter(
    (member) => member.role_id !== ROLE.CONTRACTOR && !descendantUserIds.has(member.user_id),
  );
  const localRoots = localStaff.map((member) => ({ ...member, children: [] as PersonTreeNode[] }));
  sortPersonTreeNodes(localRoots);
  let roots = [...localRoots];

  unit.children.forEach((child) => {
    roots = attachChildRoots(localRoots, roots, buildUnitPeopleTree(child));
  });

  return roots;
};
