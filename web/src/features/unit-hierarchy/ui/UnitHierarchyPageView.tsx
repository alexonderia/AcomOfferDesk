import AddOutlinedIcon from '@mui/icons-material/AddOutlined';
import ApartmentOutlinedIcon from '@mui/icons-material/ApartmentOutlined';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import Groups2OutlinedIcon from '@mui/icons-material/Groups2Outlined';
import HubOutlinedIcon from '@mui/icons-material/HubOutlined';
import LinkOffOutlinedIcon from '@mui/icons-material/LinkOffOutlined';
import PersonOutlineOutlinedIcon from '@mui/icons-material/PersonOutlineOutlined';
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Stack,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Typography,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import { useMemo, useState, type HTMLAttributes } from 'react';
import type { AvailableUnitUser, RecommendedHierarchyNode, UnitMember, UnitNode } from '@shared/api/units';
import { useUnitHierarchyPage } from '../model/useUnitHierarchyPage';
import { UnitOrgChart } from './UnitOrgChart';
import { hierarchyPageColors, sectionCardSx } from './unitHierarchyStyles';

const recommendedCardWidth = 162;
const recommendedCardHeight = 132;
const recommendedSiblingGap = 14;
const recommendedModuleGap = 2;
const recommendedRowHeight = 172;
const recommendedConnectorDrop = 22;
const recommendedForestPaddingX = 20;
const recommendedForestPaddingY = 12;

type HierarchyViewMode = 'combined' | 'units';
type UnitsViewContentMode = 'structure' | 'members';
type DepartmentFilterOption = DepartmentOption | { unitId: 'all'; name: 'Все подразделения' };

type DepartmentOption = {
  name: string;
  unitId: number;
};

type AssignedUnitInfo = {
  depth: number;
  label: string;
  unitId: number;
  unitName: string;
};

type PositionedRecommendedNode = {
  cardHeight: number;
  cardWidth: number;
  children: PositionedRecommendedNode[];
  depth: number;
  node: RecommendedHierarchyNode;
  x: number;
  y: number;
};

const isRecommendationPlaceholder = (node: RecommendedHierarchyNode) => {
  const fullName = (node.full_name ?? '').trim().toLowerCase();
  return fullName.includes('вакан') || fullName.includes('не указано');
};

const getRecommendedDescendantCount = (node: RecommendedHierarchyNode): number =>
  node.children.reduce((total, child) => total + 1 + getRecommendedDescendantCount(child), 0);

const getRecommendedCardWidthByDepth = (_depth: number) => recommendedCardWidth;

const getRecommendedCardHeightByDepth = (_depth: number) => recommendedCardHeight;

const positionRecommendedNode = (
  node: RecommendedHierarchyNode,
  depth: number,
  leafIndexRef: { value: number }
): PositionedRecommendedNode => {
  const children = node.children.map((child) => positionRecommendedNode(child, depth + 1, leafIndexRef));
  const cardWidth = getRecommendedCardWidthByDepth(depth);
  const cardHeight = getRecommendedCardHeightByDepth(depth);
  const y = depth * recommendedRowHeight;

  if (children.length === 0) {
    const x = leafIndexRef.value * (recommendedCardWidth + recommendedSiblingGap) + cardWidth / 2;
    leafIndexRef.value += 1;

    return {
      node,
      depth,
      x,
      y,
      cardWidth,
      cardHeight,
      children,
    };
  }

  const x = children.reduce((sum, child) => sum + child.x, 0) / children.length;

  return {
    node,
    depth,
    x,
    y,
    cardWidth,
    cardHeight,
    children,
  };
};

const collectRecommendedNodes = (root: PositionedRecommendedNode): PositionedRecommendedNode[] => [
  root,
  ...root.children.flatMap(collectRecommendedNodes),
];

const getRecommendedSubtreeBounds = (root: PositionedRecommendedNode) => {
  const nodes = collectRecommendedNodes(root);

  return {
    left: Math.min(...nodes.map((node) => node.x - node.cardWidth / 2)),
    right: Math.max(...nodes.map((node) => node.x + node.cardWidth / 2)),
  };
};

const shiftRecommendedSubtree = (
  node: PositionedRecommendedNode,
  shiftX: number,
  shiftY = 0
): PositionedRecommendedNode => ({
  ...node,
  x: node.x + shiftX,
  y: node.y + shiftY,
  children: node.children.map((child) => shiftRecommendedSubtree(child, shiftX, shiftY)),
});

const normalizeRecommendedForest = (roots: PositionedRecommendedNode[]) => {
  const subtreeBounds = roots.map(getRecommendedSubtreeBounds);
  let currentLeft = recommendedForestPaddingX;

  const placedRoots = roots.map((root, index) => {
    const bounds = subtreeBounds[index]!;
    const subtreeWidth = bounds.right - bounds.left;
    const placedRoot = shiftRecommendedSubtree(root, currentLeft - bounds.left, recommendedForestPaddingY);
    currentLeft += subtreeWidth + recommendedModuleGap;
    return placedRoot;
  });

  const placedNodes = placedRoots.flatMap(collectRecommendedNodes);
  const minLeft = Math.min(...placedNodes.map((node) => node.x - node.cardWidth / 2));
  const safeShiftX = minLeft < recommendedForestPaddingX ? recommendedForestPaddingX - minLeft : 0;
  const normalizedRoots = safeShiftX > 0
    ? placedRoots.map((root) => shiftRecommendedSubtree(root, safeShiftX))
    : placedRoots;

  const normalizedNodes = normalizedRoots.flatMap(collectRecommendedNodes);
  const maxRight = Math.max(...normalizedNodes.map((node) => node.x + node.cardWidth / 2));
  const maxBottom = Math.max(...normalizedNodes.map((node) => node.y + node.cardHeight));

  return {
    height: maxBottom + recommendedConnectorDrop + recommendedForestPaddingY,
    roots: normalizedRoots,
    width: maxRight + recommendedForestPaddingX,
  };
};

const RecommendedNodeCard = ({
  assignedUnits,
  canAssignToUnit,
  depth,
  node,
  onEditUnits,
  onAssignToUnit,
}: {
  assignedUnits?: AssignedUnitInfo[] | undefined;
  canAssignToUnit?: boolean;
  depth: number;
  node: RecommendedHierarchyNode;
  onEditUnits?: (() => void) | undefined;
  onAssignToUnit?: (() => void) | undefined;
}) => {
  const subordinateCount = node.children.length;
  const descendantCount = getRecommendedDescendantCount(node);
  const isPlaceholder = isRecommendationPlaceholder(node);

  return (
    <Card
      variant="outlined"
      sx={{
        width: recommendedCardWidth,
        minHeight: recommendedCardHeight,
        borderRadius: 1.8,
        borderColor: isPlaceholder ? alpha(hierarchyPageColors.softPink, 0.55) : hierarchyPageColors.cardBorder,
        backgroundColor: '#ffffff',
        boxShadow: '0 2px 8px rgba(27, 39, 57, 0.08)',
      }}
    >
      <CardContent sx={{ p: 1.05, '&:last-child': { pb: 1.05 } }}>
        <Stack spacing={0.8} sx={{ height: '100%' }}>
          <Box minWidth={0}>
            <Typography
              sx={{
                color: isPlaceholder ? hierarchyPageColors.softPink : hierarchyPageColors.textPrimary,
                fontSize: 11.3,
                fontWeight: 600,
                lineHeight: 1.22,
                overflowWrap: 'anywhere',
              }}
            >
              {node.full_name ?? node.user_id}
            </Typography>
            <Typography
              variant="body2"
              sx={{
                mt: 0.25,
                color: hierarchyPageColors.textPrimary,
                fontSize: 10.35,
                lineHeight: 1.2,
              }}
            >
              {node.role_name}
            </Typography>
            {assignedUnits && assignedUnits.length > 0 ? (
              <Stack direction="row" spacing={0.4} alignItems="flex-start" sx={{ mt: 0.75, minWidth: 0 }}>
                <Box
                  sx={{
                    flex: 1,
                    minWidth: 0,
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: 0.35,
                  }}
                >
                  {assignedUnits.map((unit) => (
                    <Typography
                      key={`${node.user_id}-${unit.unitId}`}
                      variant="caption"
                      sx={{
                        maxWidth: '100%',
                        borderRadius: 999,
                        px: 0.55,
                        py: 0.12,
                        color: unit.depth === 0 ? '#0f5b8d' : hierarchyPageColors.softTeal,
                        backgroundColor: unit.depth === 0
                          ? alpha(hierarchyPageColors.softBlue, 0.12)
                          : alpha(hierarchyPageColors.softTeal, 0.08),
                        fontSize: 9.8,
                        fontWeight: 700,
                        lineHeight: 1.25,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                      title={unit.label}
                    >
                      {unit.unitName}
                    </Typography>
                  ))}
                </Box>
                <Tooltip title="Изменить привязки">
                  <IconButton
                    size="small"
                    aria-label="Изменить привязки"
                    onClick={onEditUnits}
                    sx={{
                      width: 20,
                      height: 20,
                      flexShrink: 0,
                      border: `1px solid ${alpha(hierarchyPageColors.softBlue, 0.18)}`,
                      backgroundColor: alpha('#ffffff', 0.92),
                      color: hierarchyPageColors.softBlue,
                      '&:hover': {
                        backgroundColor: alpha(hierarchyPageColors.softBlue, 0.08),
                      },
                    }}
                  >
                    <EditOutlinedIcon sx={{ fontSize: 12.5 }} />
                  </IconButton>
                </Tooltip>
              </Stack>
            ) : null}
            {(!assignedUnits || assignedUnits.length === 0) && canAssignToUnit ? (
              <Button
                size="small"
                variant="outlined"
                onClick={onAssignToUnit}
                sx={{
                  mt: 0.75,
                  minHeight: 24,
                  px: 0.8,
                  py: 0.1,
                  alignSelf: 'flex-start',
                  borderColor: alpha(hierarchyPageColors.softBlue, 0.4),
                  color: hierarchyPageColors.softBlue,
                  fontSize: 10,
                  fontWeight: 700,
                }}
              >
                Закрепить
              </Button>
            ) : null}
          </Box>

          <Box sx={{ mt: 'auto', pt: depth === 0 ? 0.7 : 0.45 }}>
            <Stack direction="row" spacing={0.75} justifyContent="flex-end" alignItems="center">
              <Tooltip title={`Всего подчиненных: ${descendantCount}`}>
                <Stack direction="row" spacing={0.15} alignItems="center" sx={{ color: hierarchyPageColors.softBlue }}>
                  <Typography variant="caption" sx={{ fontSize: 10.4, fontWeight: 700 }}>
                    {descendantCount}
                  </Typography>
                  <Groups2OutlinedIcon sx={{ fontSize: 11.5 }} />
                </Stack>
              </Tooltip>
              <Tooltip title={`Прямых подчиненных: ${subordinateCount}`}>
                <Stack direction="row" spacing={0.15} alignItems="center" sx={{ color: hierarchyPageColors.softPink }}>
                  <Typography variant="caption" sx={{ fontSize: 10.4, fontWeight: 700 }}>
                    {subordinateCount}
                  </Typography>
                  <PersonOutlineOutlinedIcon sx={{ fontSize: 11.5 }} />
                </Stack>
              </Tooltip>
              <Tooltip title={`Уровень в дереве: ${depth + 1}`}>
                <Stack direction="row" spacing={0.15} alignItems="center" sx={{ color: alpha('#7c3aed', 0.8) }}>
                  <Typography variant="caption" sx={{ fontSize: 10.4, fontWeight: 700 }}>
                    {depth + 1}
                  </Typography>
                  <HubOutlinedIcon sx={{ fontSize: 11.5 }} />
                </Stack>
              </Tooltip>
            </Stack>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
};

const RecommendedAbsoluteTree = ({
  memberUnitByUserId,
  height,
  onAssignToUnit,
  roots,
  width,
}: {
  height: number;
  memberUnitByUserId: Record<string, AssignedUnitInfo[]>;
  onAssignToUnit: (node: RecommendedHierarchyNode) => void;
  roots: PositionedRecommendedNode[];
  width: number;
}) => {
  const renderSubtree = (current: PositionedRecommendedNode) => {
    const anchorX = current.x;
    const anchorY = current.y + current.cardHeight;
    const connectorBandY = anchorY + recommendedConnectorDrop;
    const firstChild = current.children[0] ?? null;
    const lastChild = current.children[current.children.length - 1] ?? null;
    const assignedUnits = memberUnitByUserId[current.node.user_id] ?? [];

    return (
      <Box key={current.node.user_id}>
        <Box
          sx={{
            position: 'absolute',
            left: anchorX - current.cardWidth / 2,
            top: current.y,
          }}
        >
          <RecommendedNodeCard
            assignedUnits={assignedUnits}
            canAssignToUnit={!isRecommendationPlaceholder(current.node)}
            depth={current.depth}
            node={current.node}
            onEditUnits={assignedUnits.length > 0 ? () => onAssignToUnit(current.node) : undefined}
            onAssignToUnit={() => onAssignToUnit(current.node)}
          />
        </Box>

        {current.children.length === 1 ? (
          <Box
            sx={{
              position: 'absolute',
              left: anchorX,
              top: anchorY,
              width: '1px',
              height: current.children[0]!.y - anchorY,
              transform: 'translateX(-50%)',
              backgroundColor: hierarchyPageColors.connector,
            }}
          />
        ) : null}

        {current.children.length > 1 && firstChild && lastChild ? (
          <>
            <Box
              sx={{
                position: 'absolute',
                left: anchorX,
                top: anchorY,
                width: '1px',
                height: recommendedConnectorDrop,
                transform: 'translateX(-50%)',
                backgroundColor: hierarchyPageColors.connector,
              }}
            />

            <Box
              sx={{
                position: 'absolute',
                left: Math.min(anchorX, firstChild.x),
                top: connectorBandY,
                width: Math.max(anchorX, lastChild.x) - Math.min(anchorX, firstChild.x),
                height: '1px',
                backgroundColor: hierarchyPageColors.connector,
              }}
            />

            {current.children.map((child) => (
              <Box
                key={`connector-${child.node.user_id}`}
                sx={{
                  position: 'absolute',
                  left: child.x,
                  top: connectorBandY,
                  width: '1px',
                  height: child.y - connectorBandY,
                  transform: 'translateX(-50%)',
                  backgroundColor: hierarchyPageColors.connector,
                }}
              />
            ))}
          </>
        ) : null}

        {current.children.map((child) => renderSubtree(child))}
      </Box>
    );
  };

  return (
    <Box sx={{ position: 'relative', width, height }}>
      {roots.map((root) => renderSubtree(root))}
    </Box>
  );
};

const RecommendedHierarchyForest = ({
  memberUnitByUserId,
  nodes,
  onAssignToUnit,
}: {
  memberUnitByUserId: Record<string, AssignedUnitInfo[]>;
  nodes: RecommendedHierarchyNode[];
  onAssignToUnit: (node: RecommendedHierarchyNode) => void;
}) => {
  const leafIndexRef = { value: 0 };
  const positionedRoots = nodes.map((node) => positionRecommendedNode(node, 0, leafIndexRef));
  const { roots, width, height } = normalizeRecommendedForest(positionedRoots);

  return (
    <Box
      sx={{
        width: 'max-content',
        minWidth: '100%',
        display: 'flex',
        justifyContent: 'center',
      }}
    >
      <RecommendedAbsoluteTree
        height={height}
        memberUnitByUserId={memberUnitByUserId}
        onAssignToUnit={onAssignToUnit}
        roots={roots}
        width={width}
      />
    </Box>
  );
};

const findUnitDepth = (nodes: UnitNode[], unitId: number, depth = 0): number | null => {
  for (const node of nodes) {
    if (node.unit_id === unitId) {
      return depth;
    }
    const nestedDepth = findUnitDepth(node.children, unitId, depth + 1);
    if (nestedDepth !== null) {
      return nestedDepth;
    }
  }
  return null;
};

const collectUnitNamesByDepth = (nodes: UnitNode[], targetDepth: number, depth = 0): string[] =>
  nodes.flatMap((node) => [
    ...(depth === targetDepth ? [node.name] : []),
    ...collectUnitNamesByDepth(node.children, targetDepth, depth + 1),
  ]);

const flattenUnits = (nodes: UnitNode[]): UnitNode[] =>
  nodes.flatMap((node) => [node, ...flattenUnits(node.children)]);

const buildDepartmentByUnitId = (nodes: UnitNode[]) => {
  const departmentByUnitId = new Map<number, DepartmentOption>();

  const visit = (node: UnitNode, department: DepartmentOption) => {
    departmentByUnitId.set(node.unit_id, department);
    node.children.forEach((child) => visit(child, department));
  };

  nodes.forEach((root) => {
    const department = { unitId: root.unit_id, name: root.name };
    visit(root, department);
  });

  return departmentByUnitId;
};

const buildRecommendedParentByUserId = (
  nodes: RecommendedHierarchyNode[],
  accumulator: Record<string, string | null> = {}
) => {
  nodes.forEach((node) => {
    accumulator[node.user_id] = node.id_parent_user;
    buildRecommendedParentByUserId(node.children, accumulator);
  });

  return accumulator;
};

const buildRecommendedNodeByUserId = (
  nodes: RecommendedHierarchyNode[],
  accumulator: Record<string, RecommendedHierarchyNode> = {}
) => {
  nodes.forEach((node) => {
    accumulator[node.user_id] = node;
    buildRecommendedNodeByUserId(node.children, accumulator);
  });

  return accumulator;
};

const buildHomeDepartmentByUserId = (
  assignmentsByUserId: Record<string, AssignedUnitInfo[]>,
  parentByUserId: Record<string, string | null>,
  departmentByUnitId: Map<number, DepartmentOption>
) => {
  const cache = new Map<string, number | null>();

  const resolveDepartment = (userId: string): number | null => {
    if (cache.has(userId)) {
      return cache.get(userId) ?? null;
    }

    const assignments = assignmentsByUserId[userId] ?? [];
    const rootAssignment = assignments.find((assignment) => assignment.depth === 0);
    if (rootAssignment) {
      const departmentId = departmentByUnitId.get(rootAssignment.unitId)?.unitId ?? null;
      cache.set(userId, departmentId);
      return departmentId;
    }

    const parentUserId = parentByUserId[userId];
    if (parentUserId) {
      const parentDepartmentId = resolveDepartment(parentUserId);
      if (parentDepartmentId !== null) {
        cache.set(userId, parentDepartmentId);
        return parentDepartmentId;
      }
    }

    const fallbackDepartmentId = assignments[0]
      ? (departmentByUnitId.get(assignments[0].unitId)?.unitId ?? null)
      : null;
    cache.set(userId, fallbackDepartmentId);
    return fallbackDepartmentId;
  };

  return Object.fromEntries(
    Object.keys(assignmentsByUserId).map((userId) => [userId, resolveDepartment(userId)])
  );
};

const buildDisplayAssignmentsByUserId = (
  assignmentsByUserId: Record<string, AssignedUnitInfo[]>,
  parentByUserId: Record<string, string | null>,
  homeDepartmentByUserId: Record<string, number | null>,
  departmentByUnitId: Map<number, DepartmentOption>,
  unitOptionsById: Map<number, { label: string; unitId: number }>
) =>
  Object.fromEntries(
    Object.entries(assignmentsByUserId).map(([userId, assignments]) => {
      const parentUserId = parentByUserId[userId];
      const parentAssignments = parentUserId ? (assignmentsByUserId[parentUserId] ?? []) : [];
      const homeDepartmentId = homeDepartmentByUserId[userId] ?? null;
      const effectiveAssignments = assignments
        .map((assignment) => {
          const departmentId = departmentByUnitId.get(assignment.unitId)?.unitId ?? null;
          const parentHasSameUnit = parentAssignments.some((parentAssignment) => parentAssignment.unitId === assignment.unitId);
          const isHomeDepartment = departmentId !== null && homeDepartmentId !== null && departmentId === homeDepartmentId;

          if (assignment.depth === 0 && departmentId !== null && homeDepartmentId !== null && departmentId !== homeDepartmentId) {
            return null;
          }

          if (assignment.depth > 0 && parentHasSameUnit && isHomeDepartment && departmentId !== null) {
            const rootOption = unitOptionsById.get(departmentId);
            if (!rootOption) {
              return assignment;
            }

            return {
              depth: 0,
              label: rootOption.label,
              unitId: rootOption.unitId,
              unitName: departmentByUnitId.get(departmentId)?.name ?? assignment.unitName,
            };
          }

          return assignment;
        })
        .filter((assignment): assignment is AssignedUnitInfo => assignment !== null)
        .filter((assignment, index, collection) =>
          collection.findIndex((candidate) => candidate.unitId === assignment.unitId) === index
        )
        .sort((left, right) => left.depth - right.depth || left.unitName.localeCompare(right.unitName, 'ru'));

      return [userId, effectiveAssignments];
    })
  );

const filterRecommendedNodesForDepartment = (
  nodes: RecommendedHierarchyNode[],
  departmentId: number,
  assignmentsByUserId: Record<string, AssignedUnitInfo[]>,
  departmentByUnitId: Map<number, DepartmentOption>
): RecommendedHierarchyNode[] =>
  nodes.flatMap((node) => {
    const hasAssignmentInDepartment = (assignmentsByUserId[node.user_id] ?? []).some(
      (assignment) => departmentByUnitId.get(assignment.unitId)?.unitId === departmentId
    );
    const filteredChildren = filterRecommendedNodesForDepartment(
      node.children,
      departmentId,
      assignmentsByUserId,
      departmentByUnitId
    );

    if (!hasAssignmentInDepartment) {
      return filteredChildren;
    }

    return [{
      ...node,
      children: filteredChildren,
    }];
  });

const buildDisplayTreeWithMembers = (
  tree: UnitNode[],
  assignmentsByUserId: Record<string, AssignedUnitInfo[]>
): UnitNode[] => {
  const memberByUserId = new Map<string, UnitMember>();
  const rawAssignmentsByUserId = new Map<string, AssignedUnitInfo[]>();

  const collectMembers = (nodes: UnitNode[], path: string[] = [], depth = 0) => {
    nodes.forEach((node) => {
      const nextPath = [...path, node.name];
      node.members.forEach((member) => {
        if (!memberByUserId.has(member.user_id)) {
          memberByUserId.set(member.user_id, member);
        }
        const currentAssignments = rawAssignmentsByUserId.get(member.user_id) ?? [];
        rawAssignmentsByUserId.set(member.user_id, [
          ...currentAssignments,
          {
            depth,
            label: nextPath.join(' / '),
            unitId: node.unit_id,
            unitName: node.name,
          },
        ]);
      });
      collectMembers(node.children, nextPath, depth + 1);
    });
  };

  collectMembers(tree);

  const cloneNode = (node: UnitNode): UnitNode => ({
    ...node,
    members: [],
    children: node.children.map(cloneNode),
  });

  const clonedTree = tree.map(cloneNode);
  const unitMap = new Map<number, UnitNode>();
  const registerUnits = (nodes: UnitNode[]) => {
    nodes.forEach((node) => {
      unitMap.set(node.unit_id, node);
      registerUnits(node.children);
    });
  };

  registerUnits(clonedTree);

  memberByUserId.forEach((member, userId) => {
    const assignments = assignmentsByUserId[userId] ?? rawAssignmentsByUserId.get(userId) ?? [];
    if (!member) {
      return;
    }

    assignments.forEach((assignment) => {
      const targetUnit = unitMap.get(assignment.unitId);
      if (!targetUnit) {
        return;
      }
      if (!targetUnit.members.some((existingMember) => existingMember.user_id === member.user_id)) {
        targetUnit.members.push(member);
      }
    });
  });

  return clonedTree;
};

const getCreateDialogTitle = () => 'Добавить узел';

const getUnitNameFieldLabel = () => 'Название узла';

const renderUserOption = (props: HTMLAttributes<HTMLLIElement>, option: AvailableUnitUser) => (
  <Box component="li" {...props}>
    <Stack spacing={0.25}>
      <Typography>{option.full_name ?? option.user_id}</Typography>
      <Typography variant="caption" color="text.secondary">
        {option.role_name} • {option.user_id}
      </Typography>
    </Stack>
  </Box>
);

export const UnitHierarchyPageView = () => {
  const [viewMode, setViewMode] = useState<HierarchyViewMode>('combined');
  const [unitsViewContentMode, setUnitsViewContentMode] = useState<UnitsViewContentMode>('structure');
  const [selectedDepartmentId, setSelectedDepartmentId] = useState<number | 'all'>('all');
  const [activeRecommendedNode, setActiveRecommendedNode] = useState<RecommendedHierarchyNode | null>(null);
  const [assignmentUnitByUserId, setAssignmentUnitByUserId] = useState<Record<string, number>>({});
  const {
    tree,
    recommendedTree,
    isLoading,
    error,
    recommendedError,
    canCreateRootUnit,
    unitOptions,
    memberUnitByUserId,
    unitDialogMode,
    activeUnit,
    unitName,
    setUnitName,
    isSavingUnit,
    createAssigneeSearch,
    setCreateAssigneeSearch,
    createAvailableUsers,
    selectedCreateUserId,
    setSelectedCreateUserId,
    isLoadingCreateUsers,
    isMemberDialogOpen,
    availableUsers,
    selectedUserId,
    setSelectedUserId,
    memberSearch,
    setMemberSearch,
    isLoadingUsers,
    isSavingMember,
    isAssigningRecommendedUserId,
    isDetachingRecommendedAssignmentKey,
    openCreateRootDialog,
    openCreateChildDialog,
    openRenameDialog,
    closeUnitDialog,
    submitUnit,
    deactivateUnit,
    closeMemberDialog,
    submitMember,
    deleteMember,
    assignRecommendedMemberToUnit,
    detachRecommendedMemberFromUnit,
  } = useUnitHierarchyPage();

  const selectedUser = useMemo(
    () => availableUsers.find((user) => user.user_id === selectedUserId) ?? null,
    [availableUsers, selectedUserId]
  );
  const selectedCreateUser = useMemo(
    () => createAvailableUsers.find((user) => user.user_id === selectedCreateUserId) ?? null,
    [createAvailableUsers, selectedCreateUserId]
  );
  const unitsById = useMemo(
    () => new Map(flattenUnits(tree).map((unit) => [unit.unit_id, unit])),
    [tree]
  );
  const departmentOptions = useMemo(
    () => tree.map((unit) => ({ unitId: unit.unit_id, name: unit.name })),
    [tree]
  );
  const departmentByUnitId = useMemo(
    () => buildDepartmentByUnitId(tree),
    [tree]
  );
  const departmentFilterOptions = useMemo<DepartmentFilterOption[]>(
    () => [{ unitId: 'all', name: 'Все подразделения' }, ...departmentOptions],
    [departmentOptions]
  );
  const unitOptionsById = useMemo(
    () => new Map(unitOptions.map((option) => [option.unitId, option])),
    [unitOptions]
  );
  const recommendedParentByUserId = useMemo(
    () => buildRecommendedParentByUserId(recommendedTree),
    [recommendedTree]
  );
  const recommendedNodeByUserId = useMemo(
    () => buildRecommendedNodeByUserId(recommendedTree),
    [recommendedTree]
  );
  const homeDepartmentByUserId = useMemo(
    () => buildHomeDepartmentByUserId(memberUnitByUserId, recommendedParentByUserId, departmentByUnitId),
    [departmentByUnitId, memberUnitByUserId, recommendedParentByUserId]
  );
  const displayMemberUnitByUserId = useMemo(
    () => buildDisplayAssignmentsByUserId(
      memberUnitByUserId,
      recommendedParentByUserId,
      homeDepartmentByUserId,
      departmentByUnitId,
      unitOptionsById
    ),
    [departmentByUnitId, homeDepartmentByUserId, memberUnitByUserId, recommendedParentByUserId, unitOptionsById]
  );
  const selectedDepartmentOption = useMemo<DepartmentFilterOption>(
    () => departmentFilterOptions.find((option) => option.unitId === selectedDepartmentId) ?? departmentFilterOptions[0]!,
    [departmentFilterOptions, selectedDepartmentId]
  );
  const selectedAssignmentUnitId = activeRecommendedNode ? (assignmentUnitByUserId[activeRecommendedNode.user_id] ?? 0) : 0;
  const activeUnitDepth = useMemo(
    () => (activeUnit ? findUnitDepth(tree, activeUnit.unit_id) : null),
    [activeUnit, tree]
  );
  const createDialogDepth = useMemo(() => {
    if (unitDialogMode === 'create-child') {
      return Math.min(2, (activeUnitDepth ?? 0) + 1);
    }
    return 0;
  }, [activeUnitDepth, unitDialogMode]);
  const createUnitNameSuggestions = useMemo(
    () => Array.from(new Set(collectUnitNamesByDepth(tree, createDialogDepth))),
    [createDialogDepth, tree]
  );
  const unitDialogTitle = unitDialogMode === 'rename'
    ? 'Переименовать узел'
    : getCreateDialogTitle();
  const activeRecommendedAssignments = useMemo(
    () => (activeRecommendedNode
      ? memberUnitByUserId[activeRecommendedNode.user_id] ?? []
      : []),
    [activeRecommendedNode, memberUnitByUserId]
  );
  const activeRecommendedManager = activeRecommendedNode?.id_parent_user
    ? (recommendedNodeByUserId[activeRecommendedNode.id_parent_user] ?? null)
    : null;
  const activeRecommendedManagerAssignments = useMemo(
    () => (activeRecommendedManager
      ? memberUnitByUserId[activeRecommendedManager.user_id] ?? []
      : []),
    [activeRecommendedManager, memberUnitByUserId]
  );
  const assignableUnitOptions = useMemo(() => {
    if (!activeRecommendedNode) {
      return unitOptions;
    }

    const assignedUnitIds = new Set(activeRecommendedAssignments.map((assignment) => assignment.unitId));
    return unitOptions.filter((option) => !assignedUnitIds.has(option.unitId));
  }, [activeRecommendedAssignments, activeRecommendedNode, unitOptions]);
  const selectedAssignmentUnit = assignableUnitOptions.find((option) => option.unitId === selectedAssignmentUnitId) ?? null;
  const activeRecommendedAssignableParents = activeRecommendedAssignments
    .map((assignment) => {
      const unit = unitsById.get(assignment.unitId);
      return unit && unit.actions.canCreateChild ? { assignment, unit } : null;
    })
    .filter((entry): entry is { assignment: AssignedUnitInfo; unit: UnitNode } => entry !== null);
  const filteredRecommendedTree = useMemo(
    () => (selectedDepartmentId === 'all'
      ? recommendedTree
      : filterRecommendedNodesForDepartment(
        recommendedTree,
        selectedDepartmentId,
        displayMemberUnitByUserId,
        departmentByUnitId
      )),
    [departmentByUnitId, displayMemberUnitByUserId, recommendedTree, selectedDepartmentId]
  );
  const filteredDisplayMemberUnitByUserId = useMemo(
    () => (selectedDepartmentId === 'all'
      ? displayMemberUnitByUserId
      : Object.fromEntries(
        Object.entries(displayMemberUnitByUserId)
          .map(([userId, assignments]) => {
            const filteredAssignments = assignments.filter(
              (assignment) => departmentByUnitId.get(assignment.unitId)?.unitId === selectedDepartmentId
            );
            return filteredAssignments.length > 0 ? [userId, filteredAssignments] : null;
          })
          .filter((entry): entry is [string, AssignedUnitInfo[]] => entry !== null)
      )),
    [departmentByUnitId, displayMemberUnitByUserId, selectedDepartmentId]
  );
  const filteredTree = useMemo(
    () => (selectedDepartmentId === 'all'
      ? tree
      : tree.filter((unit) => unit.unit_id === selectedDepartmentId)),
    [selectedDepartmentId, tree]
  );
  const displayTreeWithMembers = useMemo(
    () => buildDisplayTreeWithMembers(filteredTree, filteredDisplayMemberUnitByUserId),
    [filteredDisplayMemberUnitByUserId, filteredTree]
  );

  return (
    <Box>
      <Stack spacing={2}>
        {error ? <Alert severity="error">{error}</Alert> : null}

        <Card variant="outlined" sx={sectionCardSx}>
          <CardContent sx={{ p: { xs: 1.5, md: 2 } }}>
            <Stack spacing={1.5}>
              <Stack
                direction={{ xs: 'column', lg: 'row' }}
                spacing={1.5}
                justifyContent="space-between"
                alignItems={{ xs: 'stretch', lg: 'center' }}
              >
                <Stack direction="row" spacing={1.1} alignItems="center">
                  <Box
                    sx={{
                      width: 38,
                      height: 38,
                      borderRadius: 1.5,
                      display: 'grid',
                      placeItems: 'center',
                      bgcolor: 'action.hover',
                      color: 'text.secondary',
                      flexShrink: 0,
                    }}
                  >
                    <ApartmentOutlinedIcon fontSize="small" />
                  </Box>
                  <Typography variant="h6" sx={{ color: 'text.primary' }}>
                    {viewMode === 'combined' ? 'Объединенная иерархия' : 'Иерархия юнитов'}
                  </Typography>
                </Stack>

                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems={{ xs: 'stretch', sm: 'center' }}>
                  <ToggleButtonGroup
                    exclusive
                    size="small"
                    value={viewMode}
                    onChange={(_event, nextViewMode: HierarchyViewMode | null) => {
                      if (nextViewMode) {
                        setViewMode(nextViewMode);
                      }
                    }}
                  >
                    <ToggleButton value="combined">Объединенная схема</ToggleButton>
                    <ToggleButton value="units">Иерархия юнитов</ToggleButton>
                  </ToggleButtonGroup>

                  {departmentFilterOptions.length > 0 ? (
                    <Autocomplete
                      size="small"
                      options={departmentFilterOptions}
                      value={selectedDepartmentOption}
                      onChange={(_event, value) => setSelectedDepartmentId(value?.unitId ?? 'all')}
                      getOptionLabel={(option) => option.name}
                      isOptionEqualToValue={(option, value) => option.unitId === value.unitId}
                      renderInput={(params) => (
                        <TextField
                          {...params}
                          label="Подразделения"
                          placeholder="Все подразделения"
                        />
                      )}
                      sx={{ minWidth: { xs: '100%', sm: 260 } }}
                    />
                  ) : null}

                  {canCreateRootUnit ? (
                    <Button
                      variant="contained"
                      startIcon={<AddOutlinedIcon />}
                      onClick={() => openCreateRootDialog()}
                      sx={{ boxShadow: 'none' }}
                    >
                      Добавить узел
                    </Button>
                  ) : null}
                </Stack>
              </Stack>

              {viewMode === 'combined' && recommendedError ? <Alert severity="warning">{recommendedError}</Alert> : null}

              {viewMode === 'units' && filteredTree.length > 0 ? (
                <ToggleButtonGroup
                  exclusive
                  size="small"
                  value={unitsViewContentMode}
                  onChange={(_event, nextMode: UnitsViewContentMode | null) => {
                    if (nextMode) {
                      setUnitsViewContentMode(nextMode);
                    }
                  }}
                  sx={{ alignSelf: 'flex-start' }}
                >
                  <ToggleButton value="structure">Структура</ToggleButton>
                  <ToggleButton value="members">Все участники</ToggleButton>
                </ToggleButtonGroup>
              ) : null}

              {isLoading ? (
                <Box sx={{ display: 'grid', placeItems: 'center', minHeight: 260 }}>
                  <CircularProgress />
                </Box>
              ) : viewMode === 'combined' ? (
                recommendedTree.length === 0 ? (
                  <Alert severity="info">Для схемы пока не найдено активной пользовательской иерархии.</Alert>
                ) : filteredRecommendedTree.length === 0 ? (
                  <Alert severity="info">Для выбранных подразделений сотрудников в схеме пока нет.</Alert>
                ) : (
                  <Box
                    sx={{
                      overflowX: 'auto',
                      overflowY: 'hidden',
                      borderRadius: 2,
                      px: { xs: 1, md: 1.5 },
                      py: { xs: 1.5, md: 2 },
                      bgcolor: hierarchyPageColors.canvas,
                      border: '1px solid',
                      borderColor: 'divider',
                    }}
                  >
                    <Box sx={{ width: 'max-content', minWidth: '100%', mx: 'auto' }}>
                      <RecommendedHierarchyForest
                        memberUnitByUserId={memberUnitByUserId}
                        nodes={filteredRecommendedTree}
                        onAssignToUnit={(node) => setActiveRecommendedNode(node)}
                      />
                    </Box>
                  </Box>
                )
              ) : filteredTree.length === 0 ? (
                <Alert severity="info">Пока не создано ни одного юнита.</Alert>
              ) : (
                <UnitOrgChart
                  showMembers={unitsViewContentMode === 'members'}
                  showPrimaryActions={false}
                  onDeactivate={deactivateUnit}
                  onDeleteMember={deleteMember}
                  onRename={openRenameDialog}
                  tree={unitsViewContentMode === 'members' ? displayTreeWithMembers : filteredTree}
                />
              )}
            </Stack>
          </CardContent>
        </Card>

        <Dialog open={unitDialogMode !== null} onClose={closeUnitDialog} maxWidth="xs" fullWidth>
          <DialogTitle>{unitDialogTitle}</DialogTitle>
          <DialogContent>
            <Stack spacing={1.25} sx={{ pt: 0.5 }}>
              {activeUnit && unitDialogMode === 'create-child' ? (
                <Alert severity="info">
                  Новый узел будет создан внутри «{activeUnit.name}».
                </Alert>
              ) : null}
              <Autocomplete
                freeSolo
                fullWidth
                options={createUnitNameSuggestions}
                value={unitName}
                inputValue={unitName}
                onChange={(_event, value) => setUnitName(typeof value === 'string' ? value : value ?? '')}
                onInputChange={(_event, value) => setUnitName(value)}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    autoFocus
                    label={unitDialogMode === 'rename' ? 'Название' : getUnitNameFieldLabel()}
                    helperText={unitDialogMode === 'rename'
                      ? undefined
                      : 'Можно ввести новое название или выбрать уже используемое на этом уровне'}
                  />
                )}
              />
              {unitDialogMode !== 'rename' ? (
                <>
                  <Autocomplete
                    options={createAvailableUsers}
                    loading={isLoadingCreateUsers}
                    value={selectedCreateUser}
                    onChange={(_event, value) => setSelectedCreateUserId(value?.user_id ?? '')}
                    inputValue={createAssigneeSearch}
                    onInputChange={(_event, value) => setCreateAssigneeSearch(value)}
                    getOptionLabel={(option) => (option.full_name ? `${option.full_name} (${option.user_id})` : option.user_id)}
                    isOptionEqualToValue={(option, value) => option.user_id === value.user_id}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        label="Сотрудник"
                        placeholder="Начните вводить имя или логин"
                      />
                    )}
                    renderOption={renderUserOption}
                  />
                  <Typography variant="caption" color="text.secondary">
                    Сотрудника можно выбрать из любого подразделения. Поле необязательное.
                  </Typography>
                </>
              ) : null}
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={closeUnitDialog}>Отмена</Button>
            <Button onClick={submitUnit} variant="contained" disabled={isSavingUnit}>
              {isSavingUnit ? 'Сохранение...' : 'Сохранить'}
            </Button>
          </DialogActions>
        </Dialog>

        <Dialog open={activeRecommendedNode !== null} onClose={() => setActiveRecommendedNode(null)} maxWidth="sm" fullWidth>
          <DialogTitle>Настроить привязки сотрудника</DialogTitle>
          <DialogContent>
            <Stack spacing={1.5} sx={{ pt: 0.5 }}>
              {activeRecommendedNode ? (
                <Alert severity="info">
                  {activeRecommendedNode.full_name ?? activeRecommendedNode.user_id} • {activeRecommendedNode.role_name}
                </Alert>
              ) : null}
              <Box
                sx={{
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 2,
                  p: 1.25,
                  bgcolor: alpha(hierarchyPageColors.softBlue, 0.03),
                }}
              >
                <Stack spacing={0.85}>
                  <Typography variant="body2" color="text.secondary">
                    Руководитель сотрудника
                  </Typography>
                  {activeRecommendedManager ? (
                    <>
                      <Typography sx={{ fontSize: 14, fontWeight: 700, lineHeight: 1.2 }}>
                        {activeRecommendedManager.full_name ?? activeRecommendedManager.user_id}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {activeRecommendedManager.role_name}
                      </Typography>
                      {activeRecommendedManagerAssignments.length > 0 ? (
                        <Stack direction="row" spacing={0.75} useFlexGap flexWrap="wrap">
                          {activeRecommendedManagerAssignments.map((assignment) => (
                            <Box
                              key={`manager-${activeRecommendedManager.user_id}-${assignment.unitId}`}
                              sx={{
                                px: 1,
                                py: 0.45,
                                borderRadius: 999,
                                border: '1px solid',
                                borderColor: alpha(hierarchyPageColors.softBlue, 0.2),
                                bgcolor: '#fff',
                                color: 'text.primary',
                                fontSize: 12.5,
                                lineHeight: 1.2,
                              }}
                              title={assignment.label}
                            >
                              {assignment.label}
                            </Box>
                          ))}
                        </Stack>
                      ) : (
                        <Typography variant="caption" color="text.secondary">
                          Привязки руководителя не указаны.
                        </Typography>
                      )}
                    </>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      Руководитель не указан.
                    </Typography>
                  )}
                </Stack>
              </Box>
              {activeRecommendedAssignments.length > 0 ? (
                <Stack spacing={0.75}>
                  <Typography variant="body2" color="text.secondary">
                    Текущие привязки
                  </Typography>
                  <Stack spacing={0.75}>
                    {activeRecommendedAssignments.map((assignment) => (
                      <Box
                        key={`${activeRecommendedNode?.user_id ?? 'user'}-${assignment.unitId}`}
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          gap: 1,
                          px: 1,
                          py: 0.8,
                          borderRadius: 1.5,
                          border: '1px solid',
                          borderColor: assignment.depth === 0
                            ? alpha(hierarchyPageColors.softBlue, 0.24)
                            : alpha(hierarchyPageColors.softTeal, 0.22),
                          bgcolor: assignment.depth === 0
                            ? alpha(hierarchyPageColors.softBlue, 0.08)
                            : alpha(hierarchyPageColors.softTeal, 0.08),
                        }}
                      >
                        <Box sx={{ minWidth: 0 }}>
                          <Typography sx={{ fontSize: 13, fontWeight: 700, lineHeight: 1.2 }}>
                            {assignment.unitName}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {assignment.label}
                          </Typography>
                        </Box>
                        <Tooltip title="Открепить от узла">
                          <span>
                            <IconButton
                              size="small"
                              aria-label={`Открепить от ${assignment.unitName}`}
                              disabled={
                                !activeRecommendedNode
                                || isDetachingRecommendedAssignmentKey === `${activeRecommendedNode.user_id}:${assignment.unitId}`
                              }
                              onClick={async () => {
                                if (!activeRecommendedNode) {
                                  return;
                                }
                                await detachRecommendedMemberFromUnit(activeRecommendedNode.user_id, assignment.unitId);
                              }}
                              sx={{
                                color: hierarchyPageColors.softPink,
                                border: `1px solid ${alpha(hierarchyPageColors.softPink, 0.2)}`,
                                backgroundColor: '#fff',
                              }}
                            >
                              <LinkOffOutlinedIcon sx={{ fontSize: 16 }} />
                            </IconButton>
                          </span>
                        </Tooltip>
                      </Box>
                    ))}
                  </Stack>
                </Stack>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  У сотрудника пока нет привязок.
                </Typography>
              )}
              <Stack spacing={1}>
                <Typography variant="body2" color="text.secondary">
                  Что сделать
                </Typography>

                <Box
                  sx={{
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 2,
                    p: 1.25,
                    bgcolor: alpha(hierarchyPageColors.softBlue, 0.03),
                  }}
                >
                  <Stack spacing={1}>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Box
                        sx={{
                          width: 34,
                          height: 34,
                          borderRadius: 1.5,
                          display: 'grid',
                          placeItems: 'center',
                          bgcolor: alpha(hierarchyPageColors.softBlue, 0.12),
                          color: hierarchyPageColors.softBlue,
                          flexShrink: 0,
                        }}
                      >
                        <ApartmentOutlinedIcon fontSize="small" />
                      </Box>
                      <Box>
                        <Typography sx={{ fontSize: 14, fontWeight: 700, lineHeight: 1.2 }}>
                          Закрепить в существующий узел
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Найдите нужный узел и сразу добавьте сотрудника в него
                        </Typography>
                      </Box>
                    </Stack>
                    <Autocomplete
                      fullWidth
                      options={assignableUnitOptions}
                      value={selectedAssignmentUnit}
                      onChange={(_event, value) => {
                        if (!activeRecommendedNode) {
                          return;
                        }
                        setAssignmentUnitByUserId((current) => ({
                          ...current,
                          [activeRecommendedNode.user_id]: value?.unitId ?? 0,
                        }));
                      }}
                      getOptionLabel={(option) => option.label}
                      isOptionEqualToValue={(option, value) => option.unitId === value.unitId}
                      renderInput={(params) => (
                        <TextField
                          {...params}
                          label="Выберите узел"
                          placeholder="Начните вводить название узла"
                        />
                      )}
                    />
                  </Stack>
                </Box>

                {activeRecommendedAssignableParents.length > 0 ? (
                  <Box
                    sx={{
                      border: '1px solid',
                      borderColor: 'divider',
                      borderRadius: 2,
                      p: 1.25,
                      bgcolor: alpha(hierarchyPageColors.softTeal, 0.03),
                    }}
                  >
                    <Stack spacing={1}>
                      <Stack direction="row" spacing={1} alignItems="center">
                        <Box
                          sx={{
                            width: 34,
                            height: 34,
                            borderRadius: 1.5,
                            display: 'grid',
                            placeItems: 'center',
                            bgcolor: alpha(hierarchyPageColors.softTeal, 0.12),
                            color: hierarchyPageColors.softTeal,
                            flexShrink: 0,
                          }}
                        >
                          <AddOutlinedIcon fontSize="small" />
                        </Box>
                        <Box>
                          <Typography sx={{ fontSize: 14, fontWeight: 700, lineHeight: 1.2 }}>
                            Создать дочерний узел
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Выберите, внутри какого текущего узла нужно создать новую ветку
                          </Typography>
                        </Box>
                      </Stack>
                      <Stack spacing={0.75}>
                        {activeRecommendedAssignableParents.map(({ assignment, unit }) => (
                          <Box
                            key={`${unit.unit_id}-${activeRecommendedNode?.user_id ?? 'user'}`}
                            sx={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              gap: 1,
                              p: 0.9,
                              borderRadius: 1.5,
                              border: '1px solid',
                              borderColor: alpha(hierarchyPageColors.softTeal, 0.16),
                              bgcolor: '#fff',
                            }}
                          >
                            <Box sx={{ minWidth: 0 }}>
                              <Typography sx={{ fontSize: 13.2, fontWeight: 600, lineHeight: 1.2 }}>
                                {assignment.unitName}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                Новый узел появится внутри этой ветки
                              </Typography>
                            </Box>
                            <Button
                              size="small"
                              variant="outlined"
                              onClick={() => {
                                if (!activeRecommendedNode) {
                                  return;
                                }
                                const currentUserId = activeRecommendedNode.user_id;
                                setActiveRecommendedNode(null);
                                openCreateChildDialog(unit, currentUserId);
                              }}
                            >
                              Создать внутри
                            </Button>
                          </Box>
                        ))}
                      </Stack>
                    </Stack>
                  </Box>
                ) : null}
              </Stack>
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setActiveRecommendedNode(null)}>Отмена</Button>
            <Button
              variant="contained"
              disabled={!activeRecommendedNode || !selectedAssignmentUnit || isAssigningRecommendedUserId === activeRecommendedNode.user_id}
              onClick={async () => {
                if (!activeRecommendedNode || !selectedAssignmentUnit) {
                  return;
                }
                await assignRecommendedMemberToUnit(activeRecommendedNode.user_id, selectedAssignmentUnit.unitId);
                setAssignmentUnitByUserId((current) => {
                  const nextState = { ...current };
                  delete nextState[activeRecommendedNode.user_id];
                  return nextState;
                });
                setActiveRecommendedNode(null);
              }}
            >
              {activeRecommendedNode && isAssigningRecommendedUserId === activeRecommendedNode.user_id ? 'Закрепляем...' : 'Закрепить'}
            </Button>
          </DialogActions>
        </Dialog>

        <Dialog open={isMemberDialogOpen} onClose={closeMemberDialog} maxWidth="sm" fullWidth>
          <DialogTitle>Добавить участника</DialogTitle>
          <DialogContent>
            <Stack spacing={1.25} sx={{ pt: 0.5 }}>
              {activeUnit ? <Alert severity="info">Узел: «{activeUnit.name}»</Alert> : null}
              <Autocomplete
                options={availableUsers}
                loading={isLoadingUsers}
                value={selectedUser}
                onChange={(_event, value) => setSelectedUserId(value?.user_id ?? '')}
                inputValue={memberSearch}
                onInputChange={(_event, value) => setMemberSearch(value)}
                getOptionLabel={(option) => (option.full_name ? `${option.full_name} (${option.user_id})` : option.user_id)}
                isOptionEqualToValue={(option, value) => option.user_id === value.user_id}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Участник"
                    placeholder="Начните вводить имя или логин"
                  />
                )}
                renderOption={renderUserOption}
              />
              <Typography variant="caption" color="text.secondary">
                Можно выбрать сотрудника из любого подразделения.
              </Typography>
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={closeMemberDialog}>Отмена</Button>
            <Button onClick={submitMember} variant="contained" disabled={isSavingMember || !selectedUserId}>
              {isSavingMember ? 'Добавление...' : 'Добавить'}
            </Button>
          </DialogActions>
        </Dialog>
      </Stack>
    </Box>
  );
};
