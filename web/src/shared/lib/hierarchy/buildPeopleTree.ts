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

export const sortPersonTreeNodes = (list: PersonTreeNode[]) => {
  list.sort((left, right) => {
    const roleDiff = getRolePriority(right.role_id) - getRolePriority(left.role_id);
    if (roleDiff !== 0) {
      return roleDiff;
    }
    return (left.full_name ?? left.user_id).localeCompare(right.full_name ?? right.user_id, 'ru');
  });
  list.forEach((node) => sortPersonTreeNodes(node.children));
};

export const buildPeopleTree = (
  members: UnitMember[],
): PersonTreeNode[] => {
  if (members.length === 0) {
    return [];
  }

  const roots = members.map((member) => ({
    ...member,
    children: [] as PersonTreeNode[],
  }));
  sortPersonTreeNodes(roots);
  return roots;
};
