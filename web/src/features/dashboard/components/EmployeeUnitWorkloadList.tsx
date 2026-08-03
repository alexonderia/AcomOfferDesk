import { Stack } from '@mui/material';
import type { UnitNode } from '@shared/api/units';
import type { ResponsibilityEmployeeNode } from '@shared/api/users/getResponsibilityDashboard';
import { HierarchyTreeBranch } from '@shared/ui/hierarchy/HierarchyTreeBranch';
import { HIERARCHY_LIST_COMPACT_BLOCK_GAP } from '@shared/ui/hierarchy/hierarchyThemeStyles';
import type { UnavailabilityPeriodInfo } from '@shared/lib/unavailability';
import {
  buildOrphanEmployeeRoots,
  buildUnitEmployeeRoots,
  collectEmployeesAssignedToUnits,
  indexEmployeeNodes,
  unitHasDashboardStaff,
} from '../lib/buildUnitWorkloadTree';
import type { ExpandedState } from './dashboardUtils';
import { EmployeeNodeCard } from './EmployeeNodeCard';

type EmployeeUnitWorkloadListProps = {
  activeUnavailabilityByUser: Record<string, UnavailabilityPeriodInfo>;
  allUnits?: UnitNode[];
  employeeTree: ResponsibilityEmployeeNode[];
  expanded: ExpandedState;
  onToggle: (userId: string) => void;
  showOrphans?: boolean;
  statusColors: Record<string, string>;
  units: UnitNode[];
  upcomingUnavailabilityByUser: Record<string, UnavailabilityPeriodInfo>;
};

const UnitWorkloadSection = ({
  activeUnavailabilityByUser,
  expanded,
  onToggle,
  statusColors,
  unit,
  upcomingUnavailabilityByUser,
  workloadRoots,
}: {
  activeUnavailabilityByUser: Record<string, UnavailabilityPeriodInfo>;
  expanded: ExpandedState;
  onToggle: (userId: string) => void;
  statusColors: Record<string, string>;
  unit: UnitNode;
  upcomingUnavailabilityByUser: Record<string, UnavailabilityPeriodInfo>;
  workloadRoots: ResponsibilityEmployeeNode[];
}) => {
  const WorkloadBranch = ({
    level,
    node,
  }: {
    level: number;
    node: ResponsibilityEmployeeNode;
  }) => {
    const isExpanded = expanded[node.user_id] ?? false;
    const hasChildren = node.children.length > 0;

    return (
      <HierarchyTreeBranch
        variant="compact"
        content={(
          <EmployeeNodeCard
            activeUnavailabilityByUser={activeUnavailabilityByUser}
            expanded={expanded}
            level={level}
            node={node}
            onToggle={onToggle}
            renderChildren={false}
            suppressLevelIndent
            statusColors={statusColors}
            upcomingUnavailabilityByUser={upcomingUnavailabilityByUser}
          />
        )}
      >
        {hasChildren && isExpanded
          ? node.children.map((child) => (
            <WorkloadBranch key={child.user_id} level={level + 1} node={child} />
          ))
          : null}
      </HierarchyTreeBranch>
    );
  };

  if (workloadRoots.length === 0) {
    return null;
  }

  return (
    <Stack spacing={HIERARCHY_LIST_COMPACT_BLOCK_GAP}>
      {workloadRoots.map((node) => (
        <WorkloadBranch
          key={`${unit.unit_id}-${node.user_id}`}
          level={0}
          node={node}
        />
      ))}
    </Stack>
  );
};

export const EmployeeUnitWorkloadList = ({
  activeUnavailabilityByUser,
  allUnits,
  employeeTree,
  expanded,
  onToggle,
  showOrphans = true,
  statusColors,
  units,
  upcomingUnavailabilityByUser,
}: EmployeeUnitWorkloadListProps) => {
  const employeeById = indexEmployeeNodes(employeeTree);
  const employeesInUnits = collectEmployeesAssignedToUnits(allUnits ?? units);
  const orphanRoots = showOrphans ? buildOrphanEmployeeRoots(employeeTree, employeesInUnits) : [];
  const visibleRoots = units.filter((unit) => unitHasDashboardStaff(unit, employeeById));

  return (
    <Stack spacing={HIERARCHY_LIST_COMPACT_BLOCK_GAP}>
      {visibleRoots.map((unit) => (
        <UnitWorkloadSection
          key={unit.unit_id}
          activeUnavailabilityByUser={activeUnavailabilityByUser}
          expanded={expanded}
          onToggle={onToggle}
          statusColors={statusColors}
          unit={unit}
          upcomingUnavailabilityByUser={upcomingUnavailabilityByUser}
          workloadRoots={buildUnitEmployeeRoots(unit, employeeById)}
        />
      ))}
      {orphanRoots.map((node) => (
        <EmployeeNodeCard
          key={`orphan-${node.user_id}`}
          activeUnavailabilityByUser={activeUnavailabilityByUser}
          expanded={expanded}
          level={0}
          node={node}
          onToggle={onToggle}
          statusColors={statusColors}
          upcomingUnavailabilityByUser={upcomingUnavailabilityByUser}
        />
      ))}
    </Stack>
  );
};
