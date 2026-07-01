import type { UnitMember } from '@shared/api/units';
import { ROLE } from '@shared/constants/roles';

export type PersonTreeNode = UnitMember & { children: PersonTreeNode[] };

const rolePriority: Record<number, number> = {
  [ROLE.SUPERADMIN]: 6,
  [ROLE.ADMIN]: 5,
  [ROLE.PROJECT_MANAGER]: 4,
  [ROLE.LEAD_ECONOMIST]: 3,
  [ROLE.ECONOMIST]: 2,
  [ROLE.OPERATOR]: 1,
};

const getRolePriority = (roleId: number) => rolePriority[roleId] ?? 0;

const canManageRole = (managerRoleId: number, targetRoleId: number) =>
  getRolePriority(managerRoleId) > getRolePriority(targetRoleId);

const sortNodes = (list: PersonTreeNode[]) => {
  list.sort((left, right) => {
    const roleDiff = getRolePriority(right.role_id) - getRolePriority(left.role_id);
    if (roleDiff !== 0) {
      return roleDiff;
    }
    return (left.full_name ?? left.user_id).localeCompare(right.full_name ?? right.user_id, 'ru');
  });
  list.forEach((node) => sortNodes(node.children));
};

const findBestManagerInSet = (
  member: UnitMember,
  candidates: UnitMember[],
): UnitMember | null => {
  const eligible = candidates.filter(
    (candidate) =>
      candidate.user_id !== member.user_id
      && canManageRole(candidate.role_id, member.role_id),
  );
  if (eligible.length === 0) {
    return null;
  }
  return [...eligible].sort((a, b) => {
    const roleDiff = getRolePriority(b.role_id) - getRolePriority(a.role_id);
    if (roleDiff !== 0) {
      return roleDiff;
    }
    return (a.full_name ?? a.user_id).localeCompare(b.full_name ?? b.user_id, 'ru');
  })[0] ?? null;
};

export const buildPeopleTree = (members: UnitMember[]): PersonTreeNode[] => {
  if (members.length === 0) {
    return [];
  }

  const memberIds = new Set(members.map((member) => member.user_id));
  const nodes = new Map<string, PersonTreeNode>(
    members.map((member) => [member.user_id, { ...member, children: [] }]),
  );
  const childIds = new Set<string>();

  members.forEach((member) => {
    const parentId = member.id_parent_user;
    if (parentId && parentId !== member.user_id && memberIds.has(parentId)) {
      nodes.get(parentId)?.children.push(nodes.get(member.user_id)!);
      childIds.add(member.user_id);
      return;
    }

    const fallbackManager = findBestManagerInSet(member, members);
    if (fallbackManager) {
      nodes.get(fallbackManager.user_id)?.children.push(nodes.get(member.user_id)!);
      childIds.add(member.user_id);
    }
  });

  let roots = members
    .filter((member) => !childIds.has(member.user_id))
    .map((member) => nodes.get(member.user_id)!);

  if (roots.length === 0) {
    roots = members.map((member) => nodes.get(member.user_id)!);
  }

  if (roots.length > 1) {
    const sortedRoots = [...roots].sort((left, right) => getRolePriority(right.role_id) - getRolePriority(left.role_id));
    const primaryRoot = sortedRoots[0]!;
    const extraRoots = sortedRoots.slice(1);
    const detachedRoots: PersonTreeNode[] = [];

    extraRoots.forEach((root) => {
      if (canManageRole(primaryRoot.role_id, root.role_id)) {
        primaryRoot.children.push(root);
        return;
      }
      detachedRoots.push(root);
    });

    roots = [primaryRoot, ...detachedRoots];
  }

  sortNodes(roots);
  return roots;
};
