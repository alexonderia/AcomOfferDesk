import type { UnitNode } from '@shared/api/units';
import { ROLE } from '@shared/constants/roles';
import { canLeadUnitSubtree, isBusinessHierarchyRole, sortPersonTreeNodes, type PersonTreeNode } from './buildPeopleTree';

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

  const primaryRoot = localRoots.find((node) => canLeadUnitSubtree(node.role_id));

  if (!primaryRoot) {
    const peers = [...roots, ...childRoots];
    return [
      ...peers.filter((node) => isBusinessHierarchyRole(node.role_id)),
      ...peers.filter((node) => !isBusinessHierarchyRole(node.role_id)),
    ];
  }

  const businessRoots = childRoots.filter((node) => isBusinessHierarchyRole(node.role_id));
  const otherRoots = childRoots.filter((node) => !isBusinessHierarchyRole(node.role_id));
  primaryRoot.children.push(...businessRoots);
  sortPersonTreeNodes(primaryRoot.children);
  return [...roots, ...otherRoots];
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
