import type { UnitMember, UnitNode } from '@shared/api/units';
import type { UserHierarchy } from '@shared/api/users/getUserHierarchy';
import { ROLE } from '@shared/constants/roles';
import type { PersonTreeNode } from '@shared/lib/hierarchy/buildPeopleTree';

export type UserHierarchyDisplayUnit = {
  departmentName: string;
  unit: UnitNode;
};

export type UserHierarchyRelationKind = 'self' | 'manager' | 'subordinate';

const isStaffMember = (member: UnitMember) => member.role_id !== ROLE.CONTRACTOR;

export const collectUniqueStaff = (unit: UnitNode): UnitMember[] => {
  const byUserId = new Map<string, UnitMember>();

  const visit = (node: UnitNode) => {
    node.members.forEach((member) => {
      if (!isStaffMember(member)) {
        return;
      }
      if (!byUserId.has(member.user_id)) {
        byUserId.set(member.user_id, member);
      }
    });
    node.children.forEach(visit);
  };

  visit(unit);
  return [...byUserId.values()];
};

const unitSubtreeContainsUser = (unit: UnitNode, userId: string): boolean => {
  if (unit.members.some((member) => member.user_id === userId && isStaffMember(member))) {
    return true;
  }

  return unit.children.some((child) => unitSubtreeContainsUser(child, userId));
};

const unitSubtreeContainsUnitId = (unit: UnitNode, unitId: number): boolean => {
  if (unit.unit_id === unitId) {
    return true;
  }

  return unit.children.some((child) => unitSubtreeContainsUnitId(child, unitId));
};

const moduleContainsAssignedUnit = (moduleUnit: UnitNode, assignedUnitIds: Set<number>) =>
  [...assignedUnitIds].some((unitId) => unitSubtreeContainsUnitId(moduleUnit, unitId));

const departmentContainsAssignedUnit = (department: UnitNode, assignedUnitIds: Set<number>) =>
  assignedUnitIds.has(department.unit_id)
  || department.children.some((child) => moduleContainsAssignedUnit(child, assignedUnitIds));

const buildDisplayUnitsForDepartment = (
  department: UnitNode,
  userId: string,
  assignedUnitIds: Set<number>,
): UserHierarchyDisplayUnit[] => {
  const userPresent = unitSubtreeContainsUser(department, userId)
    || departmentContainsAssignedUnit(department, assignedUnitIds);

  if (!userPresent) {
    return [];
  }

  if (department.children.length === 0) {
    return [{ departmentName: department.name, unit: department }];
  }

  const moduleCards = department.children
    .filter((moduleUnit) => (
      unitSubtreeContainsUser(moduleUnit, userId)
      || moduleContainsAssignedUnit(moduleUnit, assignedUnitIds)
    ))
    .map((moduleUnit) => ({
      departmentName: department.name,
      unit: moduleUnit,
    }));

  if (moduleCards.length > 0) {
    return moduleCards;
  }

  const userAtDepartmentRoot = department.members.some(
    (member) => member.user_id === userId && isStaffMember(member),
  );

  if (userAtDepartmentRoot || assignedUnitIds.has(department.unit_id)) {
    return [{ departmentName: department.name, unit: department }];
  }

  return [];
};

export const buildUserHierarchyDisplayUnits = (
  hierarchy: UserHierarchy,
  unitsTree: UnitNode[],
): UserHierarchyDisplayUnit[] => {
  const userId = hierarchy.user.userId;
  const assignedUnitIds = new Set(hierarchy.units.map((unit) => unit.unitId));

  const cards = unitsTree.flatMap((department) =>
    buildDisplayUnitsForDepartment(department, userId, assignedUnitIds));

  const seenModuleIds = new Set<number>();
  return cards.filter((card) => {
    if (seenModuleIds.has(card.unit.unit_id)) {
      return false;
    }
    seenModuleIds.add(card.unit.unit_id);
    return true;
  });
};

const markSubordinateBranch = (
  node: PersonTreeNode,
  relationByUserId: Map<string, UserHierarchyRelationKind>,
) => {
  relationByUserId.set(node.user_id, 'subordinate');
  node.children.forEach((child) => markSubordinateBranch(child, relationByUserId));
};

const markStructuralRelations = (
  node: PersonTreeNode,
  selectedUserId: string,
  relationByUserId: Map<string, UserHierarchyRelationKind>,
): boolean => {
  if (node.user_id === selectedUserId) {
    relationByUserId.set(node.user_id, 'self');
    node.children.forEach((child) => markSubordinateBranch(child, relationByUserId));
    return true;
  }

  for (const child of node.children) {
    if (markStructuralRelations(child, selectedUserId, relationByUserId)) {
      relationByUserId.set(node.user_id, 'manager');
      return true;
    }
  }

  return false;
};

export const buildUnitRelationKinds = ({
  roots,
  selectedUserId,
}: {
  roots: PersonTreeNode[];
  selectedUserId: string;
}) => {
  const relationByUserId = new Map<string, UserHierarchyRelationKind>();
  roots.some((root) => markStructuralRelations(root, selectedUserId, relationByUserId));
  return relationByUserId;
};
