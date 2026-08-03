import type { UnitNode } from '@shared/api/units';
import { ROLE } from '@shared/constants/roles';
import type { ResponsibilityEmployeeNode } from '@shared/api/users/getResponsibilityDashboard';
import { buildUnitPeopleTree } from '@shared/lib/hierarchy/buildUnitPeopleTree';
import type { PersonTreeNode } from '@shared/lib/hierarchy/buildPeopleTree';

export const indexEmployeeNodes = (
  nodes: ResponsibilityEmployeeNode[],
): Map<string, ResponsibilityEmployeeNode> => {
  const byUserId = new Map<string, ResponsibilityEmployeeNode>();

  const visit = (node: ResponsibilityEmployeeNode) => {
    byUserId.set(node.user_id, node);
    node.children.forEach(visit);
  };

  nodes.forEach(visit);
  return byUserId;
};

const collectUnitMemberIds = (unit: UnitNode, target: Set<string>) => {
  unit.members.forEach((member) => {
    target.add(member.user_id);
  });
  unit.children.forEach((child) => collectUnitMemberIds(child, target));
};

export const collectEmployeesAssignedToUnits = (units: UnitNode[]): Set<string> => {
  const userIds = new Set<string>();
  units.forEach((unit) => collectUnitMemberIds(unit, userIds));
  return userIds;
};

const collectDashboardStaffIds = (
  unit: UnitNode,
  employeeById: Map<string, ResponsibilityEmployeeNode>,
  target: Set<string>,
) => {
  unit.members.forEach((member) => {
    if (member.role_id !== ROLE.CONTRACTOR && employeeById.has(member.user_id)) {
      target.add(member.user_id);
    }
  });
  unit.children.forEach((child) => collectDashboardStaffIds(child, employeeById, target));
};

const mapPersonNodeToEmployeeNodes = (
  node: PersonTreeNode,
  employeeById: Map<string, ResponsibilityEmployeeNode>,
): ResponsibilityEmployeeNode[] => {
  const mappedChildren = node.children.flatMap((child) => mapPersonNodeToEmployeeNodes(child, employeeById));
  const employeeNode = employeeById.get(node.user_id);

  if (!employeeNode) {
    return mappedChildren;
  }

  return [{
    ...employeeNode,
    children: mappedChildren,
  }];
};

export const buildUnitEmployeeRoots = (
  unit: UnitNode,
  employeeById: Map<string, ResponsibilityEmployeeNode>,
): ResponsibilityEmployeeNode[] =>
  buildUnitPeopleTree(unit).flatMap((node) => mapPersonNodeToEmployeeNodes(node, employeeById));

export const unitHasDashboardStaff = (
  unit: UnitNode,
  employeeById: Map<string, ResponsibilityEmployeeNode>,
): boolean => {
  const staffIds = new Set<string>();
  collectDashboardStaffIds(unit, employeeById, staffIds);
  return staffIds.size > 0;
};

export const buildOrphanEmployeeRoots = (
  tree: ResponsibilityEmployeeNode[],
  employeesInUnits: Set<string>,
): ResponsibilityEmployeeNode[] =>
  tree.filter((node) => !employeesInUnits.has(node.user_id));
