import AddOutlinedIcon from '@mui/icons-material/AddOutlined';
import ApartmentOutlinedIcon from '@mui/icons-material/ApartmentOutlined';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import Groups2OutlinedIcon from '@mui/icons-material/Groups2Outlined';
import LinkOffOutlinedIcon from '@mui/icons-material/LinkOffOutlined';
import PersonOutlineOutlinedIcon from '@mui/icons-material/PersonOutlineOutlined';
import PersonRemoveAlt1OutlinedIcon from '@mui/icons-material/PersonRemoveAlt1Outlined';
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
  createFilterOptions,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import { memo, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, type HTMLAttributes } from 'react';
import type { AvailableUnitUser, RecommendedHierarchyNode, UnitMember, UnitNode } from '@shared/api/units';
import { useUnitHierarchyPage } from '../model/useUnitHierarchyPage';
import { UnitOrgChart } from './UnitOrgChart';
import {
  connectorLineSx,
  getMemberDisplayName,
  getUnitLevelLabel,
  groupMembersForOrgChart,
  hierarchyCanvasBackground,
  hierarchyPageColors,
  sectionCardSx,
  statusLabelByCode,
} from './unitHierarchyStyles';

const recommendedMemberCardWidth = 184;
const recommendedMemberCardGap = 12;
const recommendedEmployeeCardHeight = 156;
const recommendedDepartmentGap = 20;
const recommendedModuleLevelGap = 34;
const recommendedModulePadX = 16;
const recommendedModulePadY = 12;
const recommendedFramePadX = 10;
const recommendedFramePadTop = 24;
const recommendedFramePadBottom = 12;
const UNASSIGNED_DEPT_ID = -1;
const EMPTY_SLOT_LABEL = '\u0421\u0432\u043e\u0431\u043e\u0434\u043d\u044b\u0439 \u0441\u043b\u043e\u0442';
const UNASSIGNED_DEPT_NAME = 'Не определено';
const createUnitNameAutocompleteFilter = createFilterOptions<string>({ limit: 20 });

type HierarchyViewMode = 'combined' | 'units';
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

type CombinedCardEntry = {
  assignment: AssignedUnitInfo | undefined;
  badgeLabel: string;
  canAssignToUnit: boolean;
  key: string;
  node: RecommendedHierarchyNode;
  orderIndex: number;
  orgDepth: number;
  parentUserId: string | null;
};

type CombinedModuleGroup = {
  entries: CombinedCardEntry[];
  key: string;
  name: string;
  unitId: number;
};

type CombinedDepartmentGroup = {
  deptUnitId: number;
  key: string;
  leadEntries: CombinedCardEntry[];
  modules: CombinedModuleGroup[];
  name: string;
};

type CombinedModuleTreeNode = {
  children: CombinedModuleTreeNode[];
  entry: CombinedCardEntry;
};

type PositionedModuleNode = {
  cardHeight: number;
  children: PositionedModuleNode[];
  entry: CombinedCardEntry;
  x: number;
  y: number;
};

type CombinedModuleFrame = {
  color: string;
  height: number;
  key: string;
  label: string;
  left: number;
  top: number;
  width: number;
};

type ModuleLayout = {
  frames: CombinedModuleFrame[];
  height: number;
  roots: PositionedModuleNode[];
  width: number;
};

type CombinedConnectorPair = {
  fromKey: string;
  key: string;
  toKey: string;
};

type CombinedConnectorLine = {
  key: string;
  x1: number;
  x2: number;
  y1: number;
  y2: number;
};

type RecommendedHierarchyForestProps = {
  allAssignmentsByUserId: Record<string, AssignedUnitInfo[]>;
  assignmentsByUserId: Record<string, AssignedUnitInfo[]>;
  departmentByUnitId: Map<number, DepartmentOption>;
  nodes: RecommendedHierarchyNode[];
  onAssignToUnit: (node: RecommendedHierarchyNode) => void;
  recommendedDepartmentByUserId: Record<string, number | null>;
};

const isRecommendationPlaceholder = (node: RecommendedHierarchyNode) => {
  const fullName = (node.full_name ?? '').trim().toLowerCase();
  return fullName.includes('вакан') || fullName.includes('не указано');
};

const getRecommendedDescendantCount = (node: RecommendedHierarchyNode): number =>
  node.children.reduce((total, child) => total + 1 + getRecommendedDescendantCount(child), 0);

const buildCombinedDepartmentGroups = (
  nodes: RecommendedHierarchyNode[],
  assignmentsByUserId: Record<string, AssignedUnitInfo[]>,
  departmentByUnitId: Map<number, DepartmentOption>,
  recommendedDepartmentByUserId: Record<string, number | null>
): CombinedDepartmentGroup[] => {
  const orderIndexByUserId = new Map<string, number>();
  const orgDepthByUserId = new Map<string, number>();
  const parentByUserId = new Map<string, string | null>();
  const nodeByUserId = new Map<string, RecommendedHierarchyNode>();
  let order = 0;

  const visit = (list: RecommendedHierarchyNode[], depth: number, parentUserId: string | null) => {
    list.forEach((node) => {
      if (!nodeByUserId.has(node.user_id)) {
        nodeByUserId.set(node.user_id, node);
        orderIndexByUserId.set(node.user_id, order);
        orgDepthByUserId.set(node.user_id, depth);
        parentByUserId.set(node.user_id, parentUserId);
        order += 1;
      }
      visit(node.children, depth + 1, node.user_id);
    });
  };

  visit(nodes, 0, null);

  const departmentOrder: number[] = [];
  const departmentMap = new Map<number, CombinedDepartmentGroup>();
  const moduleMap = new Map<string, CombinedModuleGroup>();

  const ensureDepartment = (deptUnitId: number, name: string) => {
    let group = departmentMap.get(deptUnitId);
    if (!group) {
      group = { deptUnitId, key: `dept:${deptUnitId}`, leadEntries: [], modules: [], name };
      departmentMap.set(deptUnitId, group);
      departmentOrder.push(deptUnitId);
    }
    return group;
  };

  const orderedUserIds = [...nodeByUserId.keys()].sort(
    (left, right) => (orderIndexByUserId.get(left) ?? 0) - (orderIndexByUserId.get(right) ?? 0)
  );

  const unassignedEntries: CombinedCardEntry[] = [];
  const buildUnassignedEntry = (node: RecommendedHierarchyNode, userId: string): CombinedCardEntry => ({
    assignment: undefined,
    badgeLabel: isRecommendationPlaceholder(node) ? EMPTY_SLOT_LABEL : UNASSIGNED_DEPT_NAME,
    canAssignToUnit: !isRecommendationPlaceholder(node),
    key: `${userId}:unassigned`,
    node,
    orderIndex: orderIndexByUserId.get(userId) ?? 0,
    orgDepth: orgDepthByUserId.get(userId) ?? 0,
    parentUserId: parentByUserId.get(userId) ?? null,
  });

  orderedUserIds.forEach((userId) => {
    const node = nodeByUserId.get(userId);
    if (!node) {
      return;
    }

    const assignments = assignmentsByUserId[userId] ?? [];

    if (assignments.length === 0) {
      const entry = buildUnassignedEntry(node, userId);
      const recommendedDepartmentId = recommendedDepartmentByUserId[userId] ?? null;
      const recommendedDepartment = recommendedDepartmentId !== null
        ? (departmentByUnitId.get(recommendedDepartmentId) ?? null)
        : null;

      if (recommendedDepartment) {
        ensureDepartment(recommendedDepartment.unitId, recommendedDepartment.name).leadEntries.push(entry);
      } else {
        unassignedEntries.push(entry);
      }
      return;
    }

    assignments.forEach((assignment, index) => {
      const department = departmentByUnitId.get(assignment.unitId);
      const deptUnitId = department?.unitId ?? assignment.unitId;
      const deptName = department?.name ?? assignment.unitName;
      const group = ensureDepartment(deptUnitId, deptName);
      const entry: CombinedCardEntry = {
        assignment,
        badgeLabel: assignment.label,
        canAssignToUnit: !isRecommendationPlaceholder(node),
        key: `${userId}:${assignment.unitId}:${index}`,
        node,
        orderIndex: orderIndexByUserId.get(userId) ?? 0,
        orgDepth: orgDepthByUserId.get(userId) ?? 0,
        parentUserId: parentByUserId.get(userId) ?? null,
      };

      if (assignment.depth === 0) {
        group.leadEntries.push(entry);
        return;
      }

      const moduleKey = `${deptUnitId}:${assignment.unitId}`;
      let moduleGroup = moduleMap.get(moduleKey);
      if (!moduleGroup) {
        moduleGroup = { entries: [], key: moduleKey, name: assignment.unitName, unitId: assignment.unitId };
        moduleMap.set(moduleKey, moduleGroup);
        group.modules.push(moduleGroup);
      }
      moduleGroup.entries.push(entry);
    });
  });

  const sortEntries = (entries: CombinedCardEntry[]) =>
    entries.sort(
      (left, right) =>
        left.orgDepth - right.orgDepth
        || left.orderIndex - right.orderIndex
        || (left.node.full_name ?? left.node.user_id).localeCompare(right.node.full_name ?? right.node.user_id, 'ru')
    );

  const orderedGroups = departmentOrder.map((deptUnitId) => {
    const group = departmentMap.get(deptUnitId)!;
    sortEntries(group.leadEntries);
    group.modules.forEach((moduleGroup) => sortEntries(moduleGroup.entries));
    return group;
  });

  if (unassignedEntries.length > 0) {
    sortEntries(unassignedEntries);
    orderedGroups.push({
      deptUnitId: UNASSIGNED_DEPT_ID,
      key: `dept:${UNASSIGNED_DEPT_ID}`,
      leadEntries: unassignedEntries,
      modules: [],
      name: UNASSIGNED_DEPT_NAME,
    });
  }

  return orderedGroups;
};

const buildCombinedDepartmentTree = (group: CombinedDepartmentGroup): CombinedModuleTreeNode[] => {
  const entries: CombinedCardEntry[] = [
    ...group.leadEntries,
    ...group.modules.flatMap((moduleGroup) => moduleGroup.entries),
  ];

  const nodeByKey = new Map<string, CombinedModuleTreeNode>();
  entries.forEach((entry) => {
    nodeByKey.set(entry.key, { children: [], entry });
  });

  const entriesByUserId = new Map<string, CombinedCardEntry[]>();
  entries.forEach((entry) => {
    const list = entriesByUserId.get(entry.node.user_id) ?? [];
    list.push(entry);
    entriesByUserId.set(entry.node.user_id, list);
  });

  const roots: CombinedModuleTreeNode[] = [];
  entries.forEach((entry) => {
    const treeNode = nodeByKey.get(entry.key)!;
    const parentUserId = entry.parentUserId;
    const candidates = parentUserId ? (entriesByUserId.get(parentUserId) ?? []) : [];

    if (candidates.length === 0) {
      roots.push(treeNode);
      return;
    }

    // Prefer the manager's card in the same module, otherwise the manager's
    // shallowest card (the department-level one), so module leads attach to РП.
    const sameModule = candidates.filter((candidate) => candidate.assignment?.unitId === entry.assignment?.unitId);
    const pool = sameModule.length > 0 ? sameModule : candidates;
    const parentEntry = [...pool].sort(
      (left, right) => (left.assignment?.depth ?? 0) - (right.assignment?.depth ?? 0) || left.orderIndex - right.orderIndex
    )[0]!;
    const parentNode = nodeByKey.get(parentEntry.key);

    if (!parentNode || parentNode === treeNode) {
      roots.push(treeNode);
      return;
    }

    parentNode.children.push(treeNode);
  });

  const sortNodes = (list: CombinedModuleTreeNode[]) => {
    list.sort(
      (left, right) =>
        (left.entry.assignment?.depth ?? 0) - (right.entry.assignment?.depth ?? 0)
        || left.entry.orgDepth - right.entry.orgDepth
        || left.entry.orderIndex - right.entry.orderIndex
    );
    list.forEach((node) => sortNodes(node.children));
  };

  sortNodes(roots);
  return roots;
};

const layoutCombinedModuleTree = (
  roots: CombinedModuleTreeNode[],
  cardHeights: Record<string, number>
): ModuleLayout => {
  const getCardHeight = (entryKey: string) => cardHeights[entryKey] ?? recommendedEmployeeCardHeight;

  const maxHeightByDepth: number[] = [];
  const measureDepths = (node: CombinedModuleTreeNode, depth: number) => {
    maxHeightByDepth[depth] = Math.max(maxHeightByDepth[depth] ?? 0, getCardHeight(node.entry.key));
    node.children.forEach((child) => measureDepths(child, depth + 1));
  };
  roots.forEach((root) => measureDepths(root, 0));

  const yByDepth: number[] = [];
  let currentTop = recommendedModulePadY;
  maxHeightByDepth.forEach((rowHeight, depth) => {
    yByDepth[depth] = currentTop;
    currentTop += rowHeight + recommendedModuleLevelGap;
  });

  let cursorX = recommendedModulePadX;
  const place = (node: CombinedModuleTreeNode, depth: number): PositionedModuleNode => {
    const cardHeight = getCardHeight(node.entry.key);
    const y = yByDepth[depth] ?? recommendedModulePadY;

    if (node.children.length === 0) {
      const x = cursorX + recommendedMemberCardWidth / 2;
      cursorX += recommendedMemberCardWidth + recommendedMemberCardGap;
      return { cardHeight, children: [], entry: node.entry, x, y };
    }

    const children = node.children.map((child) => place(child, depth + 1));
    const x = (children[0]!.x + children[children.length - 1]!.x) / 2;
    return { cardHeight, children, entry: node.entry, x, y };
  };

  const positionedRoots = roots.map((root) => place(root, 0));
  const positionedNodes = positionedRoots.flatMap(flattenPositionedModuleNodes);

  const framesByUnit = new Map<number, { entry: CombinedCardEntry; nodes: PositionedModuleNode[] }>();
  positionedNodes.forEach((positionedNode) => {
    const assignment = positionedNode.entry.assignment;
    if (!assignment || assignment.depth === 0) {
      return;
    }
    const unitId = assignment.unitId;
    const bucket = framesByUnit.get(unitId) ?? { entry: positionedNode.entry, nodes: [] };
    bucket.nodes.push(positionedNode);
    framesByUnit.set(unitId, bucket);
  });

  const frames: CombinedModuleFrame[] = [...framesByUnit.entries()].map(([unitId, bucket]) => {
    const left = Math.min(...bucket.nodes.map((node) => node.x - recommendedMemberCardWidth / 2)) - recommendedFramePadX;
    const right = Math.max(...bucket.nodes.map((node) => node.x + recommendedMemberCardWidth / 2)) + recommendedFramePadX;
    const top = Math.min(...bucket.nodes.map((node) => node.y)) - recommendedFramePadTop;
    const bottom = Math.max(...bucket.nodes.map((node) => node.y + node.cardHeight)) + recommendedFramePadBottom;

    return {
      color: hierarchyPageColors.softTeal,
      height: bottom - top,
      key: `frame:${unitId}`,
      label: bucket.entry.assignment?.unitName ?? '',
      left,
      top,
      width: right - left,
    };
  });

  const lastDepth = maxHeightByDepth.length - 1;
  const height = lastDepth >= 0
    ? (yByDepth[lastDepth] ?? 0) + (maxHeightByDepth[lastDepth] ?? 0) + recommendedModulePadY
    : recommendedModulePadY * 2;
  const width = Math.max(
    recommendedMemberCardWidth + recommendedModulePadX * 2,
    cursorX - recommendedMemberCardGap + recommendedModulePadX
  );

  return { frames, height, roots: positionedRoots, width };
};

const flattenPositionedModuleNodes = (node: PositionedModuleNode): PositionedModuleNode[] => [
  node,
  ...node.children.flatMap(flattenPositionedModuleNodes),
];

const buildCombinedConnectorPairs = (groups: CombinedDepartmentGroup[]): CombinedConnectorPair[] => {
  const allEntries: { deptUnitId: number; entry: CombinedCardEntry }[] = [];

  groups.forEach((group) => {
    group.leadEntries.forEach((entry) => allEntries.push({ deptUnitId: group.deptUnitId, entry }));
    group.modules.forEach((moduleGroup) =>
      moduleGroup.entries.forEach((entry) => allEntries.push({ deptUnitId: group.deptUnitId, entry }))
    );
  });

  const entriesByUserId = new Map<string, { deptUnitId: number; entry: CombinedCardEntry }[]>();
  allEntries.forEach((item) => {
    const list = entriesByUserId.get(item.entry.node.user_id) ?? [];
    list.push(item);
    entriesByUserId.set(item.entry.node.user_id, list);
  });

  const pairs: CombinedConnectorPair[] = [];
  const emittedChildUserIds = new Set<string>();
  allEntries.forEach(({ deptUnitId, entry }) => {
    const parentUserId = entry.parentUserId;
    if (!parentUserId) {
      return;
    }

    const candidates = entriesByUserId.get(parentUserId) ?? [];
    if (candidates.length === 0) {
      return;
    }

    const sameDepartment = candidates.filter((candidate) => candidate.deptUnitId === deptUnitId);
    if (sameDepartment.length > 0) {
      // Manager has a card in the same department: the department org graph draws this edge.
      return;
    }

    // The person's "main" placement is a department where the manager is also present
    // (that edge is drawn inside the department graph). Duplicate cards that live in
    // other departments must not get a dangling cross-department connector.
    const parentDepartmentIds = new Set(candidates.map((candidate) => candidate.deptUnitId));
    const childCards = entriesByUserId.get(entry.node.user_id) ?? [];
    const hasMainPlacement = childCards.some((card) => parentDepartmentIds.has(card.deptUnitId));
    if (hasMainPlacement) {
      return;
    }

    // The person lives entirely outside the manager's departments: keep a single link.
    if (emittedChildUserIds.has(entry.node.user_id)) {
      return;
    }

    const target = [...candidates].sort(
      (left, right) =>
        (left.entry.assignment?.depth ?? 0) - (right.entry.assignment?.depth ?? 0)
        || left.entry.orgDepth - right.entry.orgDepth
        || left.entry.orderIndex - right.entry.orderIndex
    )[0];

    if (!target || target.entry.key === entry.key) {
      return;
    }

    emittedChildUserIds.add(entry.node.user_id);
    pairs.push({ fromKey: target.entry.key, key: `${target.entry.key}->${entry.key}`, toKey: entry.key });
  });

  return pairs;
};

const RecommendedEmployeeDuplicateCard = ({
  assignment,
  badgeLabels,
  activeLabel,
  canAssignToUnit,
  node,
  onAssignToUnit,
}: {
  assignment?: AssignedUnitInfo | undefined;
  badgeLabels: string[];
  activeLabel?: string | undefined;
  canAssignToUnit: boolean;
  node: RecommendedHierarchyNode;
  onAssignToUnit?: (() => void) | undefined;
}) => {
  const isPlaceholder = isRecommendationPlaceholder(node);
  const subordinateCount = node.children.length;
  const descendantCount = getRecommendedDescendantCount(node);

  return (
    <Box
      sx={{
        width: recommendedMemberCardWidth,
        minHeight: recommendedEmployeeCardHeight,
        borderRadius: 2,
        border: `1px solid ${
          isPlaceholder ? alpha(hierarchyPageColors.softPink, 0.5) : alpha(hierarchyPageColors.cardBorder, 0.92)
        }`,
        backgroundColor: '#ffffff',
        px: 1,
        py: 0.95,
        boxShadow: '0 1px 3px rgba(15, 23, 42, 0.06)',
      }}
    >
      <Stack spacing={0.72} sx={{ height: '100%' }}>
        <Stack
          direction="row"
          spacing={0.45}
          useFlexGap
          flexWrap="wrap"
          sx={{ alignSelf: 'flex-start', maxWidth: '100%' }}
        >
          {badgeLabels.map((label) => {
            const isActiveBadge = activeLabel !== undefined && label === activeLabel;
            return (
              <Box
                key={label}
                sx={{
                  maxWidth: '100%',
                  px: 0.95,
                  py: 0.42,
                  borderRadius: 999,
                  border: '1px solid',
                  borderColor: assignment
                    ? alpha(hierarchyPageColors.softBlue, isActiveBadge ? 0.42 : 0.22)
                    : alpha(hierarchyPageColors.canvasBorder, 0.88),
                  backgroundColor: assignment
                    ? alpha(hierarchyPageColors.softBlue, isActiveBadge ? 0.14 : 0.06)
                    : alpha(hierarchyPageColors.canvas, 0.75),
                }}
              >
                <Typography
                  variant="caption"
                  sx={{
                    display: 'block',
                    color: assignment ? hierarchyPageColors.softBlue : hierarchyPageColors.textSecondary,
                    fontSize: 9.9,
                    fontWeight: 700,
                    lineHeight: 1.15,
                    overflowWrap: 'anywhere',
                  }}
                >
                  {label}
                </Typography>
              </Box>
            );
          })}
        </Stack>

        <Stack direction="row" spacing={0.6} justifyContent="space-between" alignItems="flex-start">
          <Box sx={{ minWidth: 0 }}>
            <Typography
              sx={{
                color: isPlaceholder ? hierarchyPageColors.softPink : hierarchyPageColors.textPrimary,
                fontSize: 12.2,
                fontWeight: 700,
                lineHeight: 1.22,
                overflowWrap: 'anywhere',
              }}
            >
              {node.full_name ?? node.user_id}
            </Typography>
          </Box>
          {canAssignToUnit && onAssignToUnit ? (
            <Tooltip
              title={
                assignment
                  ? `\u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c \u043f\u0440\u0438\u0432\u044f\u0437\u043a\u0438 ${assignment.unitName}`
                  : '\u0417\u0430\u043f\u043e\u043b\u043d\u0438\u0442\u044c \u0431\u043b\u043e\u043a'
              }
            >
              <IconButton
                size="small"
                aria-label={assignment
                  ? `\u0418\u0437\u043c\u0435\u043d\u0438\u0442\u044c \u043f\u0440\u0438\u0432\u044f\u0437\u043a\u0438 ${node.full_name ?? node.user_id} / ${assignment.unitName}`
                  : `\u0417\u0430\u043f\u043e\u043b\u043d\u0438\u0442\u044c \u0431\u043b\u043e\u043a ${node.full_name ?? node.user_id}`}
                onClick={onAssignToUnit}
                sx={{
                  width: 24,
                  height: 24,
                  flexShrink: 0,
                  color: hierarchyPageColors.softBlue,
                  border: `1px solid ${alpha(hierarchyPageColors.softBlue, 0.16)}`,
                  backgroundColor: '#ffffff',
                }}
              >
                <EditOutlinedIcon sx={{ fontSize: 12.5 }} />
              </IconButton>
            </Tooltip>
          ) : null}
        </Stack>

        <Typography
          variant="caption"
          sx={{
            display: 'block',
            color: hierarchyPageColors.textPrimary,
            fontSize: 10.35,
            fontWeight: 500,
            lineHeight: 1.2,
          }}
        >
          {node.role_name}
        </Typography>

        <Typography
          variant="caption"
          sx={{
            display: 'block',
            color: alpha(hierarchyPageColors.textSecondary, 0.88),
            fontSize: 9.8,
            lineHeight: 1.2,
          }}
        >
          {node.user_id}
        </Typography>

        <Box
          sx={{
            mt: 'auto',
            pt: 0.55,
            borderTop: `1px solid ${alpha(hierarchyPageColors.canvasBorder, 0.68)}`,
          }}
        >
          <Stack direction="row" spacing={0.7} justifyContent="flex-end" alignItems="center">
            <Stack
              direction="row"
              spacing={0.3}
              alignItems="center"
              sx={{
                color: hierarchyPageColors.softBlue,
                px: 0.55,
                py: 0.2,
                borderRadius: 999,
                backgroundColor: alpha(hierarchyPageColors.softBlue, 0.06),
              }}
            >
              <Typography variant="caption" sx={{ fontSize: 10.1, fontWeight: 700 }}>
                {descendantCount}
              </Typography>
              <Groups2OutlinedIcon sx={{ fontSize: 11 }} />
            </Stack>
            <Stack
              direction="row"
              spacing={0.3}
              alignItems="center"
              sx={{
                color: hierarchyPageColors.softPink,
                px: 0.55,
                py: 0.2,
                borderRadius: 999,
                backgroundColor: alpha(hierarchyPageColors.softPink, 0.06),
              }}
            >
              <Typography variant="caption" sx={{ fontSize: 10.1, fontWeight: 700 }}>
                {subordinateCount}
              </Typography>
              <PersonOutlineOutlinedIcon sx={{ fontSize: 11 }} />
            </Stack>
          </Stack>
        </Box>
      </Stack>
    </Box>
  );
};

const RecommendedHierarchyForestComponent = ({
  allAssignmentsByUserId,
  assignmentsByUserId,
  departmentByUnitId,
  nodes,
  onAssignToUnit,
  recommendedDepartmentByUserId,
}: RecommendedHierarchyForestProps) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const cardRefs = useRef(new Map<string, HTMLDivElement>());
  const [connectorLines, setConnectorLines] = useState<CombinedConnectorLine[]>([]);
  const [cardHeights, setCardHeights] = useState<Record<string, number>>({});

  const groups = useMemo(
    () => buildCombinedDepartmentGroups(
      nodes,
      assignmentsByUserId,
      departmentByUnitId,
      recommendedDepartmentByUserId
    ),
    [assignmentsByUserId, departmentByUnitId, nodes, recommendedDepartmentByUserId]
  );
  const connectorPairs = useMemo(() => buildCombinedConnectorPairs(groups), [groups]);
  const departmentLayoutByKey = useMemo(() => {
    const layouts = new Map<string, ModuleLayout>();
    groups.forEach((group) => {
      const tree = buildCombinedDepartmentTree(group);
      layouts.set(group.key, layoutCombinedModuleTree(tree, cardHeights));
    });
    return layouts;
  }, [cardHeights, groups]);

  useLayoutEffect(() => {
    const measureHeights = () => {
      setCardHeights((current) => {
        let changed = false;
        const next: Record<string, number> = { ...current };
        cardRefs.current.forEach((element, key) => {
          const height = element.getBoundingClientRect().height;
          if (height > 0 && Math.abs((current[key] ?? 0) - height) > 0.5) {
            next[key] = height;
            changed = true;
          }
        });
        return changed ? next : current;
      });
    };

    measureHeights();

    const container = containerRef.current;
    let resizeObserver: ResizeObserver | null = null;
    if (container && typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(measureHeights);
      resizeObserver.observe(container);
    }

    return () => {
      resizeObserver?.disconnect();
    };
  }, [groups]);

  useLayoutEffect(() => {
    const container = containerRef.current;
    if (!container) {
      return undefined;
    }

    const computeConnectors = () => {
      const base = container.getBoundingClientRect();
      const nextLines: CombinedConnectorLine[] = [];

      connectorPairs.forEach((pair) => {
        const fromElement = cardRefs.current.get(pair.fromKey);
        const toElement = cardRefs.current.get(pair.toKey);
        if (!fromElement || !toElement) {
          return;
        }

        const fromRect = fromElement.getBoundingClientRect();
        const toRect = toElement.getBoundingClientRect();
        nextLines.push({
          key: pair.key,
          x1: fromRect.left + fromRect.width / 2 - base.left,
          x2: toRect.left + toRect.width / 2 - base.left,
          y1: fromRect.bottom - base.top,
          y2: toRect.top - base.top,
        });
      });

      setConnectorLines(nextLines);
    };

    computeConnectors();

    const handleResize = () => computeConnectors();
    let resizeObserver: ResizeObserver | null = null;
    if (typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(computeConnectors);
      resizeObserver.observe(container);
    }
    window.addEventListener('resize', handleResize);

    return () => {
      resizeObserver?.disconnect();
      window.removeEventListener('resize', handleResize);
    };
  }, [connectorPairs, departmentLayoutByKey]);

  const registerCardRef = (key: string) => (element: HTMLDivElement | null) => {
    if (element) {
      cardRefs.current.set(key, element);
    } else {
      cardRefs.current.delete(key);
    }
  };

  const renderEntry = (entry: CombinedCardEntry) => {
    const memberships = allAssignmentsByUserId[entry.node.user_id] ?? [];
    const badgeLabels = entry.assignment && memberships.length > 0
      ? Array.from(new Set(memberships.map((membership) => membership.label)))
      : [entry.badgeLabel];

    return (
      <Box
        key={entry.key}
        ref={registerCardRef(entry.key)}
        sx={{ position: 'relative', zIndex: 1, width: recommendedMemberCardWidth }}
      >
        <RecommendedEmployeeDuplicateCard
          assignment={entry.assignment}
          badgeLabels={badgeLabels}
          activeLabel={entry.assignment?.label}
          canAssignToUnit={entry.canAssignToUnit}
          node={entry.node}
          onAssignToUnit={entry.canAssignToUnit ? () => onAssignToUnit(entry.node) : undefined}
        />
      </Box>
    );
  };

  const renderModuleConnectors = (node: PositionedModuleNode): JSX.Element[] => {
    if (node.children.length === 0) {
      return [];
    }

    const parentBottom = node.y + node.cardHeight;
    const childTop = node.children[0]!.y;
    const busY = parentBottom + Math.max(8, (childTop - parentBottom) / 2);
    const segments: JSX.Element[] = [
      <Box
        key={`${node.entry.key}-stub`}
        sx={{ ...connectorLineSx, position: 'absolute', left: node.x, top: parentBottom, width: '1px', height: busY - parentBottom, transform: 'translateX(-50%)' }}
      />,
    ];

    if (node.children.length === 1) {
      const child = node.children[0]!;
      segments.push(
        <Box
          key={`${node.entry.key}-drop`}
          sx={{ ...connectorLineSx, position: 'absolute', left: child.x, top: busY, width: '1px', height: child.y - busY, transform: 'translateX(-50%)' }}
        />
      );
    } else {
      const first = node.children[0]!;
      const last = node.children[node.children.length - 1]!;
      segments.push(
        <Box
          key={`${node.entry.key}-bus`}
          sx={{ ...connectorLineSx, position: 'absolute', left: first.x, top: busY, width: last.x - first.x, height: '1px' }}
        />
      );
      node.children.forEach((child) => {
        segments.push(
          <Box
            key={`${node.entry.key}-${child.entry.key}-drop`}
            sx={{ ...connectorLineSx, position: 'absolute', left: child.x, top: busY, width: '1px', height: child.y - busY, transform: 'translateX(-50%)' }}
          />
        );
      });
    }

    node.children.forEach((child) => {
      segments.push(...renderModuleConnectors(child));
    });

    return segments;
  };

  const renderDepartmentGraph = (layout: ModuleLayout | undefined) => {
    if (!layout) {
      return null;
    }

    const positionedNodes = layout.roots.flatMap(flattenPositionedModuleNodes);

    return (
      <Box sx={{ position: 'relative', width: layout.width, height: layout.height }}>
        {layout.frames.map((frame) => (
          <Box
            key={frame.key}
            sx={{
              position: 'absolute',
              left: frame.left,
              top: frame.top,
              width: frame.width,
              height: frame.height,
              borderRadius: 2,
              border: `1px dashed ${alpha(frame.color, 0.32)}`,
              backgroundColor: alpha(frame.color, 0.025),
              zIndex: 0,
              pointerEvents: 'none',
            }}
          >
            <Box
              sx={{
                position: 'absolute',
                top: -12,
                left: 12,
                px: 0.8,
                py: 0.25,
                borderRadius: 999,
                border: `1px solid ${alpha(frame.color, 0.14)}`,
                backgroundColor: '#ffffff',
                color: frame.color,
                fontSize: 11,
                fontWeight: 700,
                lineHeight: 1.2,
                whiteSpace: 'nowrap',
              }}
            >
              {frame.label}
            </Box>
          </Box>
        ))}

        {layout.roots.flatMap(renderModuleConnectors)}

        {positionedNodes.map((positionedNode) => (
          <Box
            key={positionedNode.entry.key}
            sx={{
              position: 'absolute',
              left: positionedNode.x - recommendedMemberCardWidth / 2,
              top: positionedNode.y,
              zIndex: 1,
            }}
          >
            {renderEntry(positionedNode.entry)}
          </Box>
        ))}
      </Box>
    );
  };

  return (
    <Box
      ref={containerRef}
      sx={{
        position: 'relative',
        width: 'max-content',
        minWidth: '100%',
        display: 'flex',
        flexWrap: 'wrap',
        gap: `${recommendedDepartmentGap}px`,
        alignItems: 'flex-start',
      }}
    >
      <Box
        component="svg"
        sx={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          pointerEvents: 'none',
          overflow: 'visible',
          zIndex: 0,
        }}
      >
        {connectorLines.map((line) => {
          const midY = line.x1 === line.x2
            ? line.y2
            : Math.max(line.y1 + 10, (line.y1 + line.y2) / 2);

          return (
            <path
              key={line.key}
              d={`M ${line.x1} ${line.y1} L ${line.x1} ${midY} L ${line.x2} ${midY} L ${line.x2} ${line.y2}`}
              fill="none"
              stroke={hierarchyPageColors.connector}
              strokeWidth={1.5}
              strokeOpacity={0.62}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          );
        })}
      </Box>

      {groups.map((group) => (
        <Box
          key={group.key}
          sx={{
            position: 'relative',
            zIndex: 1,
            borderRadius: 2.5,
            border: `1px solid ${alpha(group.deptUnitId === UNASSIGNED_DEPT_ID ? hierarchyPageColors.canvasBorder : hierarchyPageColors.softBlue, 0.4)}`,
            backgroundColor: '#ffffff',
            boxShadow: '0 1px 2px rgba(15, 23, 42, 0.05)',
            p: 1.55,
            display: 'flex',
            flexDirection: 'column',
            gap: 1.25,
            alignSelf: 'stretch',
          }}
        >
          <Box
            sx={{
              alignSelf: 'flex-start',
              px: 0.9,
              py: 0.3,
              borderRadius: 999,
              border: `1px solid ${alpha(group.deptUnitId === UNASSIGNED_DEPT_ID ? hierarchyPageColors.canvasBorder : hierarchyPageColors.softBlue, 0.18)}`,
              backgroundColor: alpha(group.deptUnitId === UNASSIGNED_DEPT_ID ? hierarchyPageColors.canvas : hierarchyPageColors.softBlue, 0.06),
              color: group.deptUnitId === UNASSIGNED_DEPT_ID ? hierarchyPageColors.textSecondary : hierarchyPageColors.softBlue,
              fontSize: 11.5,
              fontWeight: 700,
              lineHeight: 1.2,
            }}
          >
            {group.name}
          </Box>

          {renderDepartmentGraph(departmentLayoutByKey.get(group.key))}
        </Box>
      ))}
    </Box>
  );
};

const RecommendedHierarchyForest = memo(RecommendedHierarchyForestComponent);
RecommendedHierarchyForest.displayName = 'RecommendedHierarchyForest';

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

const buildUnitParentById = (
  nodes: UnitNode[],
  parentUnitId: number | null = null,
  accumulator: Map<number, number | null> = new Map()
): Map<number, number | null> => {
  nodes.forEach((node) => {
    accumulator.set(node.unit_id, parentUnitId);
    buildUnitParentById(node.children, node.unit_id, accumulator);
  });
  return accumulator;
};

const isAncestorUnit = (
  parentByUnitId: Map<number, number | null>,
  ancestorUnitId: number,
  descendantUnitId: number
): boolean => {
  let cursor = parentByUnitId.get(descendantUnitId) ?? null;
  const visited = new Set<number>();
  while (cursor !== null && !visited.has(cursor)) {
    if (cursor === ancestorUnitId) {
      return true;
    }
    visited.add(cursor);
    cursor = parentByUnitId.get(cursor) ?? null;
  }
  return false;
};

// On the combined chart a separate card for a parent unit is redundant when the same
// person is already shown in one of its child units, so drop the ancestor assignment.
const pruneRedundantAncestorAssignments = (
  assignmentsByUserId: Record<string, AssignedUnitInfo[]>,
  parentByUnitId: Map<number, number | null>
): Record<string, AssignedUnitInfo[]> =>
  Object.fromEntries(
    Object.entries(assignmentsByUserId).map(([userId, assignments]) => {
      if (assignments.length <= 1) {
        return [userId, assignments];
      }
      const pruned = assignments.filter(
        (assignment) => !assignments.some(
          (other) => other.unitId !== assignment.unitId
            && isAncestorUnit(parentByUnitId, assignment.unitId, other.unitId)
        )
      );
      return [userId, pruned.length > 0 ? pruned : assignments];
    })
  );

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

const buildRecommendedDepartmentByUserId = (
  nodes: RecommendedHierarchyNode[],
  assignmentsByUserId: Record<string, AssignedUnitInfo[]>,
  parentByUserId: Record<string, string | null>,
  departmentByUnitId: Map<number, DepartmentOption>
) => {
  const childUserIdsByUserId: Record<string, string[]> = {};

  const visit = (list: RecommendedHierarchyNode[]) => {
    list.forEach((node) => {
      childUserIdsByUserId[node.user_id] = node.children.map((child) => child.user_id);
      visit(node.children);
    });
  };

  visit(nodes);

  const cache = new Map<string, number | null>();
  const resolvingUserIds = new Set<string>();

  const resolveDepartment = (userId: string): number | null => {
    if (cache.has(userId)) {
      return cache.get(userId) ?? null;
    }

    if (resolvingUserIds.has(userId)) {
      return null;
    }

    resolvingUserIds.add(userId);

    const assignments = assignmentsByUserId[userId] ?? [];
    const rootAssignment = assignments.find((assignment) => assignment.depth === 0);
    if (rootAssignment) {
      const departmentId = departmentByUnitId.get(rootAssignment.unitId)?.unitId ?? null;
      cache.set(userId, departmentId);
      resolvingUserIds.delete(userId);
      return departmentId;
    }

    const parentUserId = parentByUserId[userId];
    if (parentUserId) {
      const parentDepartmentId = resolveDepartment(parentUserId);
      if (parentDepartmentId !== null) {
        cache.set(userId, parentDepartmentId);
        resolvingUserIds.delete(userId);
        return parentDepartmentId;
      }
    }

    const fallbackDepartmentId = assignments[0]
      ? (departmentByUnitId.get(assignments[0].unitId)?.unitId ?? null)
      : null;
    if (fallbackDepartmentId !== null) {
      cache.set(userId, fallbackDepartmentId);
      resolvingUserIds.delete(userId);
      return fallbackDepartmentId;
    }

    const childDepartmentId = (childUserIdsByUserId[userId] ?? [])
      .map((childUserId) => resolveDepartment(childUserId))
      .find((departmentId): departmentId is number => departmentId !== null);
    if (childDepartmentId !== undefined) {
      cache.set(userId, childDepartmentId);
      resolvingUserIds.delete(userId);
      return childDepartmentId;
    }

    cache.set(userId, fallbackDepartmentId);
    resolvingUserIds.delete(userId);
    return fallbackDepartmentId;
  };

  return Object.fromEntries(
    Object.keys(parentByUserId).map((userId) => [userId, resolveDepartment(userId)])
  );
};

const filterRecommendedNodesForDepartment = (
  nodes: RecommendedHierarchyNode[],
  departmentId: number,
  assignmentsByUserId: Record<string, AssignedUnitInfo[]>,
  departmentByUnitId: Map<number, DepartmentOption>,
  recommendedDepartmentByUserId: Record<string, number | null>
): RecommendedHierarchyNode[] =>
  nodes.flatMap((node) => {
    const hasAssignmentInDepartment = (assignmentsByUserId[node.user_id] ?? []).some(
      (assignment) => departmentByUnitId.get(assignment.unitId)?.unitId === departmentId
    );
    const hasAnyAssignment = (assignmentsByUserId[node.user_id] ?? []).length > 0;
    const inheritsDepartment = !hasAnyAssignment && recommendedDepartmentByUserId[node.user_id] === departmentId;
    const filteredChildren = filterRecommendedNodesForDepartment(
      node.children,
      departmentId,
      assignmentsByUserId,
      departmentByUnitId,
      recommendedDepartmentByUserId
    );

    if (!hasAssignmentInDepartment && !inheritsDepartment) {
      return filteredChildren;
    }

    return [{
      ...node,
      children: filteredChildren,
    }];
  });

type UnitDialogMode = 'create-root' | 'create-child' | 'rename' | null;

type UnitDialogProps = {
  activeUnit: UnitNode | null;
  initialCreateUserId: string;
  isSaving: boolean;
  loadCreateAvailableUsers: (searchValue?: string) => Promise<AvailableUnitUser[]>;
  mode: UnitDialogMode;
  onClose: () => void;
  onSubmit: (unitName: string, selectedCreateUserId?: string) => Promise<void>;
  tree: UnitNode[];
};

const UnitDialog = memo(({
  activeUnit,
  initialCreateUserId,
  isSaving,
  loadCreateAvailableUsers,
  mode,
  onClose,
  onSubmit,
  tree,
}: UnitDialogProps) => {
  const [unitName, setUnitName] = useState('');
  const [createAssigneeSearch, setCreateAssigneeSearch] = useState('');
  const [createAvailableUsers, setCreateAvailableUsers] = useState<AvailableUnitUser[]>([]);
  const [selectedCreateUserId, setSelectedCreateUserId] = useState('');
  const [isLoadingCreateUsers, setIsLoadingCreateUsers] = useState(false);

  useEffect(() => {
    if (mode === null) {
      return;
    }

    setUnitName(mode === 'rename' ? (activeUnit?.name ?? '') : '');
    setCreateAssigneeSearch('');
    setCreateAvailableUsers([]);
    setSelectedCreateUserId(initialCreateUserId);
  }, [activeUnit, initialCreateUserId, mode]);

  useEffect(() => {
    if (mode === null || mode === 'rename') {
      return;
    }

    let isActive = true;
    setIsLoadingCreateUsers(true);

    void loadCreateAvailableUsers()
      .then((users) => {
        if (isActive) {
          setCreateAvailableUsers(users);
        }
      })
      .finally(() => {
        if (isActive) {
          setIsLoadingCreateUsers(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, [loadCreateAvailableUsers, mode]);

  const selectedCreateUser = useMemo(
    () => createAvailableUsers.find((user) => user.user_id === selectedCreateUserId) ?? null,
    [createAvailableUsers, selectedCreateUserId]
  );
  const activeUnitDepth = useMemo(
    () => (activeUnit ? findUnitDepth(tree, activeUnit.unit_id) : null),
    [activeUnit, tree]
  );
  const createDialogDepth = useMemo(() => {
    if (mode === 'create-child') {
      return Math.min(2, (activeUnitDepth ?? 0) + 1);
    }
    return 0;
  }, [activeUnitDepth, mode]);
  const createUnitNameSuggestions = useMemo(
    () => Array.from(new Set(collectUnitNamesByDepth(tree, createDialogDepth))),
    [createDialogDepth, tree]
  );
  const selectedCreateUnitNameSuggestion = useMemo(
    () => createUnitNameSuggestions.find((option) => option === unitName) ?? null,
    [createUnitNameSuggestions, unitName]
  );
  const isRootLevel = mode === 'rename' ? activeUnitDepth === 0 : createDialogDepth === 0;
  const entityWord = isRootLevel ? 'подразделение' : 'объединение';
  const title = mode === 'rename' ? `Переименовать ${entityWord}` : `Добавить ${entityWord}`;

  return (
    <Dialog open={mode !== null} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent dividers>
        <Stack spacing={1.25}>
          <Autocomplete
            freeSolo
            fullWidth
            filterOptions={createUnitNameAutocompleteFilter}
            options={createUnitNameSuggestions}
            value={selectedCreateUnitNameSuggestion}
            inputValue={unitName}
            onChange={(_event, value) => setUnitName(typeof value === 'string' ? value : value ?? '')}
            onInputChange={(_event, value, reason) => {
              if (reason === 'input' || reason === 'clear') {
                setUnitName(value);
              }
            }}
            renderInput={(params) => (
              <TextField
                {...params}
                autoFocus
                label={mode === 'rename' ? 'Название' : `Название ${isRootLevel ? 'подразделения' : 'объединения'}`}
              />
            )}
          />
          {mode !== 'rename' ? (
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
          ) : null}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Отмена</Button>
        <Button
          onClick={() => void onSubmit(unitName, selectedCreateUserId || undefined)}
          variant="contained"
          disabled={isSaving}
        >
          {isSaving ? 'Сохранение...' : 'Сохранить'}
        </Button>
      </DialogActions>
    </Dialog>
  );
});

UnitDialog.displayName = 'UnitDialog';

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

const filterAssignmentsByDepartment = (
  assignmentsByUserId: Record<string, AssignedUnitInfo[]>,
  departmentByUnitId: Map<number, DepartmentOption>,
  selectedDepartmentId: number | 'all'
) => {
  if (selectedDepartmentId === 'all') {
    return assignmentsByUserId;
  }

  return Object.fromEntries(
    Object.entries(assignmentsByUserId)
      .map(([userId, assignments]) => {
        const filteredAssignments = assignments.filter(
          (assignment) => departmentByUnitId.get(assignment.unitId)?.unitId === selectedDepartmentId
        );
        return filteredAssignments.length > 0 ? [userId, filteredAssignments] : null;
      })
      .filter((entry): entry is [string, AssignedUnitInfo[]] => entry !== null)
  );
};

const UnitMemberCard = ({
  member,
  canManage,
  onRemove,
}: {
  member: UnitMember;
  canManage: boolean;
  onRemove: () => void;
}) => (
  <Card variant="outlined" sx={{ boxShadow: 'none' }}>
    <CardContent
      sx={{
        p: 1.2,
        '&:last-child': { pb: 1.2 },
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        gap: 1,
      }}
    >
      <Box sx={{ minWidth: 0 }}>
        <Typography sx={{ fontSize: 13.5, fontWeight: 700, lineHeight: 1.2, overflowWrap: 'anywhere' }}>
          {getMemberDisplayName(member)}
        </Typography>
        <Typography variant="caption" sx={{ display: 'block', mt: 0.2, color: 'text.primary' }}>
          {member.role_name}
        </Typography>
        <Typography variant="caption" sx={{ display: 'block', mt: 0.35, color: 'text.secondary' }}>
          {statusLabelByCode[member.status] ?? member.status} • {member.user_id}
        </Typography>
      </Box>
      {canManage ? (
        <Tooltip title="Удалить участника">
          <span>
            <IconButton
              size="small"
              aria-label={`Удалить участника ${getMemberDisplayName(member)}`}
              onClick={onRemove}
              sx={{
                color: hierarchyPageColors.softPink,
                border: '1px solid',
                borderColor: 'divider',
                backgroundColor: 'background.paper',
              }}
            >
              <PersonRemoveAlt1OutlinedIcon sx={{ fontSize: 16 }} />
            </IconButton>
          </span>
        </Tooltip>
      ) : null}
    </CardContent>
  </Card>
);

const UnitMemberSection = ({
  title,
  accentColor,
  members,
  canManage,
  onRemoveMember,
}: {
  title: string;
  accentColor: string;
  members: UnitMember[];
  canManage: boolean;
  onRemoveMember: (member: UnitMember) => void;
}) => {
  if (members.length === 0) {
    return null;
  }

  return (
    <Stack spacing={0.75}>
      <Stack direction="row" spacing={0.75} alignItems="center">
        <Box sx={{ width: 8, height: 8, borderRadius: 999, backgroundColor: accentColor }} />
        <Typography sx={{ fontSize: 12.5, fontWeight: 700, color: 'text.secondary', letterSpacing: 0.2 }}>
          {title}
        </Typography>
        <Box
          sx={{
            ml: 0.25,
            px: 0.75,
            py: 0.1,
            borderRadius: 999,
            backgroundColor: alpha(accentColor, 0.1),
            color: accentColor,
            fontSize: 11,
            fontWeight: 700,
            lineHeight: 1.4,
          }}
        >
          {members.length}
        </Box>
      </Stack>
      <Stack spacing={0.9}>
        {members.map((member) => (
          <UnitMemberCard
            key={member.user_id}
            member={member}
            canManage={canManage}
            onRemove={() => onRemoveMember(member)}
          />
        ))}
      </Stack>
    </Stack>
  );
};

export const UnitHierarchyPageView = () => {
  const [viewMode, setViewMode] = useState<HierarchyViewMode>('combined');
  const [selectedDepartmentId, setSelectedDepartmentId] = useState<number | 'all'>('all');
  const [activeRecommendedNode, setActiveRecommendedNode] = useState<RecommendedHierarchyNode | null>(null);
  const [activeUnitDetailsId, setActiveUnitDetailsId] = useState<number | null>(null);
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
    initialCreateUserId,
    isSavingUnit,
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
    loadCreateAvailableUsers,
    openCreateRootDialog,
    openCreateChildDialog,
    openRenameDialog,
    closeUnitDialog,
    submitUnit,
    deactivateUnit,
    openMemberDialog,
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
  const parentByUnitId = useMemo(
    () => buildUnitParentById(tree),
    [tree]
  );
  const departmentFilterOptions = useMemo<DepartmentFilterOption[]>(
    () => [{ unitId: 'all', name: 'Все подразделения' }, ...departmentOptions],
    [departmentOptions]
  );
  const recommendedParentByUserId = useMemo(
    () => buildRecommendedParentByUserId(recommendedTree),
    [recommendedTree]
  );
  const recommendedNodeByUserId = useMemo(
    () => buildRecommendedNodeByUserId(recommendedTree),
    [recommendedTree]
  );
  const recommendedDepartmentByUserId = useMemo(
    () => buildRecommendedDepartmentByUserId(
      recommendedTree,
      memberUnitByUserId,
      recommendedParentByUserId,
      departmentByUnitId
    ),
    [departmentByUnitId, memberUnitByUserId, recommendedParentByUserId, recommendedTree]
  );
  const selectedDepartmentOption = useMemo<DepartmentFilterOption>(
    () => departmentFilterOptions.find((option) => option.unitId === selectedDepartmentId) ?? departmentFilterOptions[0]!,
    [departmentFilterOptions, selectedDepartmentId]
  );
  const selectedAssignmentUnitId = activeRecommendedNode ? (assignmentUnitByUserId[activeRecommendedNode.user_id] ?? 0) : 0;
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
  const handleAssignRecommendedNode = useCallback((node: RecommendedHierarchyNode) => {
    setActiveRecommendedNode(node);
  }, []);
  const handleOpenUnitDetails = useCallback((unit: UnitNode) => {
    setActiveUnitDetailsId(unit.unit_id);
  }, []);
  const activeRecommendedAssignableParents = activeRecommendedAssignments
    .map((assignment) => {
      const unit = unitsById.get(assignment.unitId);
      return unit && unit.actions.canCreateChild ? { assignment, unit } : null;
    })
    .filter((entry): entry is { assignment: AssignedUnitInfo; unit: UnitNode } => entry !== null);
  const filteredCombinedAssignmentsByUserId = useMemo(
    () => pruneRedundantAncestorAssignments(
      filterAssignmentsByDepartment(memberUnitByUserId, departmentByUnitId, selectedDepartmentId),
      parentByUnitId
    ),
    [departmentByUnitId, memberUnitByUserId, parentByUnitId, selectedDepartmentId]
  );
  const filteredRecommendedTree = useMemo(
    () => (selectedDepartmentId === 'all'
      ? recommendedTree
      : filterRecommendedNodesForDepartment(
        recommendedTree,
        selectedDepartmentId,
        filteredCombinedAssignmentsByUserId,
        departmentByUnitId,
        recommendedDepartmentByUserId
      )),
    [departmentByUnitId, filteredCombinedAssignmentsByUserId, recommendedDepartmentByUserId, recommendedTree, selectedDepartmentId]
  );
  const filteredTree = useMemo(
    () => (selectedDepartmentId === 'all'
      ? tree
      : tree.filter((unit) => unit.unit_id === selectedDepartmentId)),
    [selectedDepartmentId, tree]
  );
  const displayedUnitsById = useMemo(
    () => new Map(flattenUnits(filteredTree).map((unit) => [unit.unit_id, unit])),
    [filteredTree]
  );
  const activeUnitDetails = activeUnitDetailsId !== null
    ? (displayedUnitsById.get(activeUnitDetailsId) ?? unitsById.get(activeUnitDetailsId) ?? null)
    : null;
  const activeUnitDetailsGroups = useMemo(() => {
    if (!activeUnitDetails) {
      return { staff: [] as UnitMember[], contractors: [] as UnitMember[] };
    }

    const { contractors, leaders, team } = groupMembersForOrgChart(activeUnitDetails.members);
    return { staff: [...leaders, ...team], contractors };
  }, [activeUnitDetails]);
  const activeUnitDetailsMembers = useMemo(
    () => [...activeUnitDetailsGroups.staff, ...activeUnitDetailsGroups.contractors],
    [activeUnitDetailsGroups]
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
                    {viewMode === 'combined' ? 'Объединенная иерархия' : 'Иерархия объединений'}
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
                    <ToggleButton value="units">Иерархия объединений</ToggleButton>
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
                      Добавить подразделение
                    </Button>
                  ) : null}
                </Stack>
              </Stack>

              {viewMode === 'combined' && recommendedError ? <Alert severity="warning">{recommendedError}</Alert> : null}

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
                      borderRadius: 2.5,
                      px: { xs: 1, md: 1.5 },
                      py: { xs: 1.5, md: 2 },
                      bgcolor: hierarchyPageColors.canvas,
                      backgroundImage: hierarchyCanvasBackground,
                      border: '1px solid',
                      borderColor: alpha(hierarchyPageColors.canvasBorder, 0.95),
                    }}
                  >
                    <Box sx={{ width: 'max-content', minWidth: '100%', mx: 'auto' }}>
                      <RecommendedHierarchyForest
                        allAssignmentsByUserId={memberUnitByUserId}
                        assignmentsByUserId={filteredCombinedAssignmentsByUserId}
                        departmentByUnitId={departmentByUnitId}
                        nodes={filteredRecommendedTree}
                        onAssignToUnit={handleAssignRecommendedNode}
                        recommendedDepartmentByUserId={recommendedDepartmentByUserId}
                      />
                    </Box>
                  </Box>
                )
              ) : filteredTree.length === 0 ? (
                <Alert severity="info">Пока не создано ни одного объединения.</Alert>
              ) : (
                <Box
                  sx={{
                    display: 'grid',
                    gridTemplateColumns: { xs: '1fr', xl: 'minmax(0, 1fr) 360px' },
                    gap: 1.5,
                    alignItems: 'start',
                  }}
                >
                  <UnitOrgChart
                    onCreateChild={openCreateChildDialog}
                    onDeactivate={deactivateUnit}
                    onOpenMemberDialog={openMemberDialog}
                    onOpenUnitDetails={handleOpenUnitDetails}
                    onRename={openRenameDialog}
                    showPrimaryActions={false}
                    tree={filteredTree}
                  />

                  <Card
                    variant="outlined"
                    role="complementary"
                    aria-label="Состав объединения"
                    sx={{
                      borderRadius: 3,
                      boxShadow: 'none',
                      position: { xl: 'sticky' },
                      top: { xl: 16 },
                    }}
                  >
                    <CardContent sx={{ p: 1.5 }}>
                      <Stack spacing={1.5}>
                        <Typography sx={{ fontSize: 16, fontWeight: 700, lineHeight: 1.2 }}>
                          Состав объединения
                        </Typography>

                        {activeUnitDetails ? (
                          <>
                            <Alert severity="info" variant="outlined">
                              «{activeUnitDetails.name}»
                            </Alert>

                            <Stack direction="row" spacing={0.75} useFlexGap flexWrap="wrap">
                              <Box
                                sx={{
                                  borderRadius: 999,
                                  px: 1,
                                  py: 0.4,
                                  backgroundColor: alpha(hierarchyPageColors.softBlue, 0.08),
                                  color: hierarchyPageColors.softBlue,
                                  fontSize: 12,
                                  fontWeight: 700,
                                  lineHeight: 1.2,
                                }}
                              >
                                Сотрудники: {activeUnitDetailsGroups.staff.length}
                              </Box>
                              {activeUnitDetailsGroups.contractors.length > 0 ? (
                                <Box
                                  sx={{
                                    borderRadius: 999,
                                    px: 1,
                                    py: 0.4,
                                    backgroundColor: alpha(hierarchyPageColors.softPink, 0.08),
                                    color: hierarchyPageColors.softPink,
                                    fontSize: 12,
                                    fontWeight: 700,
                                    lineHeight: 1.2,
                                  }}
                                >
                                  Контрагенты: {activeUnitDetailsGroups.contractors.length}
                                </Box>
                              ) : null}
                              <Box
                                sx={{
                                  borderRadius: 999,
                                  px: 1,
                                  py: 0.4,
                                  backgroundColor: alpha(hierarchyPageColors.softTeal, 0.08),
                                  color: hierarchyPageColors.softTeal,
                                  fontSize: 12,
                                  fontWeight: 700,
                                  lineHeight: 1.2,
                                }}
                              >
                                Вложенные объединения: {activeUnitDetails.children.length}
                              </Box>
                            </Stack>

                            <Stack direction="row" justifyContent="flex-end" alignItems="center" spacing={1}>
                              {activeUnitDetails.actions.canManageMembers ? (
                                <Button
                                  size="small"
                                  variant="outlined"
                                  startIcon={<AddOutlinedIcon />}
                                  onClick={() => openMemberDialog(activeUnitDetails)}
                                >
                                  Добавить сотрудника
                                </Button>
                              ) : null}
                            </Stack>

                            {activeUnitDetailsMembers.length > 0 ? (
                              <Stack spacing={1.4}>
                                <UnitMemberSection
                                  title="Сотрудники"
                                  accentColor={hierarchyPageColors.softBlue}
                                  members={activeUnitDetailsGroups.staff}
                                  canManage={activeUnitDetails.actions.canManageMembers}
                                  onRemoveMember={(member) => {
                                    void deleteMember(activeUnitDetails, member);
                                  }}
                                />
                                <UnitMemberSection
                                  title="Контрагенты"
                                  accentColor={hierarchyPageColors.softPink}
                                  members={activeUnitDetailsGroups.contractors}
                                  canManage={activeUnitDetails.actions.canManageMembers}
                                  onRemoveMember={(member) => {
                                    void deleteMember(activeUnitDetails, member);
                                  }}
                                />
                              </Stack>
                            ) : (
                              <Box
                                sx={{
                                  borderRadius: 2,
                                  border: '1px dashed',
                                  borderColor: 'divider',
                                  backgroundColor: 'background.default',
                                  px: 1.25,
                                  py: 1.1,
                                }}
                              >
                                <Typography variant="body2" color="text.secondary">
                                  Участников нет.
                                </Typography>
                              </Box>
                            )}
                          </>
                        ) : (
                          <Box
                            sx={{
                              borderRadius: 2.5,
                              border: '1px dashed',
                              borderColor: alpha(hierarchyPageColors.canvasBorder, 0.95),
                              backgroundColor: alpha(hierarchyPageColors.canvas, 0.72),
                              px: 1.4,
                              py: 1.6,
                            }}
                          >
                            <Stack spacing={0.8}>
                              <Typography sx={{ fontSize: 14, fontWeight: 700, lineHeight: 1.25 }}>
                                Выберите объединение
                              </Typography>
                            </Stack>
                          </Box>
                        )}
                      </Stack>
                    </CardContent>
                  </Card>
                </Box>
              )}
            </Stack>
          </CardContent>
        </Card>

        <UnitDialog
          activeUnit={activeUnit}
          initialCreateUserId={initialCreateUserId}
          isSaving={isSavingUnit}
          loadCreateAvailableUsers={loadCreateAvailableUsers}
          mode={unitDialogMode}
          onClose={closeUnitDialog}
          onSubmit={submitUnit}
          tree={tree}
        />

        <Dialog open={activeRecommendedNode !== null} onClose={() => setActiveRecommendedNode(null)} maxWidth="sm" fullWidth>
          <DialogTitle>
            {activeRecommendedNode
              ? (activeRecommendedNode.full_name ?? activeRecommendedNode.user_id)
              : 'Настроить привязки'}
          </DialogTitle>
          <DialogContent dividers>
            <Stack spacing={1.5}>
              <Card variant="outlined" sx={{ boxShadow: 'none' }}>
                <CardContent sx={{ p: 1.4, '&:last-child': { pb: 1.4 } }}>
                  <Stack spacing={0.85}>
                    <Typography variant="body2" color="text.secondary">
                      Руководитель
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
                                  borderColor: 'divider',
                                  bgcolor: 'background.default',
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
                            Привязок нет
                          </Typography>
                        )}
                      </>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        Не указан
                      </Typography>
                    )}
                  </Stack>
                </CardContent>
              </Card>

              {activeRecommendedAssignments.length > 0 ? (
                <Stack spacing={0.75}>
                  <Typography variant="body2" color="text.secondary">
                    Привязки
                  </Typography>
                  <Stack spacing={0.75}>
                    {activeRecommendedAssignments.map((assignment) => (
                      <Card
                        key={`${activeRecommendedNode?.user_id ?? 'user'}-${assignment.unitId}`}
                        variant="outlined"
                        sx={{ boxShadow: 'none' }}
                      >
                        <CardContent
                          sx={{
                            p: 1.1,
                            '&:last-child': { pb: 1.1 },
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            gap: 1,
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
                                  border: '1px solid',
                                  borderColor: 'divider',
                                  backgroundColor: 'background.paper',
                                }}
                              >
                                <LinkOffOutlinedIcon sx={{ fontSize: 16 }} />
                              </IconButton>
                            </span>
                          </Tooltip>
                        </CardContent>
                      </Card>
                    ))}
                  </Stack>
                </Stack>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Привязок нет.
                </Typography>
              )}

              <Stack spacing={1}>
                <Card variant="outlined" sx={{ boxShadow: 'none' }}>
                  <CardContent sx={{ p: 1.3, '&:last-child': { pb: 1.3 } }}>
                    <Stack spacing={1}>
                      <Stack direction="row" spacing={1} alignItems="center">
                        <Box
                          sx={{
                            width: 34,
                            height: 34,
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
                        <Box>
                          <Typography sx={{ fontSize: 14, fontWeight: 700, lineHeight: 1.2 }}>
                            Закрепить в объединение
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
                            label="Выберите объединение"
                            placeholder="Начните вводить название объединения"
                          />
                        )}
                      />
                    </Stack>
                  </CardContent>
                </Card>

                {activeRecommendedAssignableParents.length > 0 ? (
                  <Card variant="outlined" sx={{ boxShadow: 'none' }}>
                    <CardContent sx={{ p: 1.3, '&:last-child': { pb: 1.3 } }}>
                      <Stack spacing={1}>
                        <Stack direction="row" spacing={1} alignItems="center">
                          <Box
                            sx={{
                              width: 34,
                              height: 34,
                              borderRadius: 1.5,
                              display: 'grid',
                              placeItems: 'center',
                              bgcolor: 'action.hover',
                              color: 'text.secondary',
                              flexShrink: 0,
                            }}
                          >
                            <AddOutlinedIcon fontSize="small" />
                        </Box>
                        <Box>
                          <Typography sx={{ fontSize: 14, fontWeight: 700, lineHeight: 1.2 }}>
                            Создать дочернее объединение
                          </Typography>
                        </Box>
                      </Stack>
                        <Stack spacing={0.75}>
                          {activeRecommendedAssignableParents.map(({ assignment, unit }) => (
                            <Card key={`${unit.unit_id}-${activeRecommendedNode?.user_id ?? 'user'}`} variant="outlined" sx={{ boxShadow: 'none' }}>
                              <CardContent
                                sx={{
                                  p: 1,
                                  '&:last-child': { pb: 1 },
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'space-between',
                                  gap: 1,
                                }}
                              >
                                <Box sx={{ minWidth: 0 }}>
                                  <Typography sx={{ fontSize: 13.2, fontWeight: 600, lineHeight: 1.2 }}>
                                    {assignment.unitName}
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
                                  Создать
                                </Button>
                              </CardContent>
                            </Card>
                          ))}
                        </Stack>
                      </Stack>
                    </CardContent>
                  </Card>
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

        <Dialog open={false} onClose={() => setActiveUnitDetailsId(null)} maxWidth="md" fullWidth>
          <DialogTitle>Состав объединения</DialogTitle>
          <DialogContent dividers>
            <Stack spacing={1.5}>
              {activeUnitDetails ? (
                <Alert severity="info" variant="outlined">
                  {getUnitLevelLabel(findUnitDepth(tree, activeUnitDetails.unit_id) ?? 0)}: «{activeUnitDetails.name}»
                </Alert>
              ) : null}

              {activeUnitDetails ? (
                <Stack direction="row" spacing={0.75} useFlexGap flexWrap="wrap">
                  <Box
                    sx={{
                      borderRadius: 999,
                      px: 1,
                      py: 0.4,
                      backgroundColor: alpha(hierarchyPageColors.softBlue, 0.08),
                      color: hierarchyPageColors.softBlue,
                      fontSize: 12,
                      fontWeight: 700,
                      lineHeight: 1.2,
                    }}
                  >
                    Участники: {activeUnitDetailsMembers.length}
                  </Box>
                  <Box
                    sx={{
                      borderRadius: 999,
                      px: 1,
                      py: 0.4,
                      backgroundColor: alpha(hierarchyPageColors.softTeal, 0.08),
                      color: hierarchyPageColors.softTeal,
                      fontSize: 12,
                      fontWeight: 700,
                      lineHeight: 1.2,
                    }}
                  >
                    Вложенные объединения: {activeUnitDetails.children.length}
                  </Box>
                </Stack>
              ) : null}

              <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={1}>
                <Typography variant="body2" color="text.secondary">
                  Участники объединения
                </Typography>
                {activeUnitDetails?.actions.canManageMembers ? (
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<AddOutlinedIcon />}
                    onClick={() => {
                      if (!activeUnitDetails) {
                        return;
                      }
                      openMemberDialog(activeUnitDetails);
                    }}
                  >
                    Добавить сотрудника
                  </Button>
                ) : null}
              </Stack>

              {activeUnitDetailsMembers.length > 0 ? (
                <Stack spacing={0.9}>
                  {activeUnitDetailsMembers.map((member) => (
                    <Card key={`${activeUnitDetails?.unit_id ?? 'unit'}-${member.user_id}`} variant="outlined" sx={{ boxShadow: 'none' }}>
                      <CardContent
                        sx={{
                          p: 1.2,
                          '&:last-child': { pb: 1.2 },
                          display: 'flex',
                          alignItems: 'flex-start',
                          justifyContent: 'space-between',
                          gap: 1,
                        }}
                      >
                        <Box sx={{ minWidth: 0 }}>
                          <Typography sx={{ fontSize: 13.5, fontWeight: 700, lineHeight: 1.2, overflowWrap: 'anywhere' }}>
                            {getMemberDisplayName(member)}
                          </Typography>
                          <Typography variant="caption" sx={{ display: 'block', mt: 0.2, color: 'text.primary' }}>
                            {member.role_name}
                          </Typography>
                          <Typography variant="caption" sx={{ display: 'block', mt: 0.35, color: 'text.secondary' }}>
                            {statusLabelByCode[member.status] ?? member.status} • {member.user_id}
                          </Typography>
                        </Box>
                        {activeUnitDetails?.actions.canManageMembers ? (
                          <Tooltip title="Удалить участника">
                            <span>
                              <IconButton
                                size="small"
                                aria-label={`Удалить участника ${getMemberDisplayName(member)}`}
                                onClick={() => {
                                  if (!activeUnitDetails) {
                                    return;
                                  }
                                  void deleteMember(activeUnitDetails, member);
                                }}
                                sx={{
                                  color: hierarchyPageColors.softPink,
                                  border: '1px solid',
                                  borderColor: 'divider',
                                  backgroundColor: 'background.paper',
                                }}
                              >
                                <PersonRemoveAlt1OutlinedIcon sx={{ fontSize: 16 }} />
                              </IconButton>
                            </span>
                          </Tooltip>
                        ) : null}
                      </CardContent>
                    </Card>
                  ))}
                </Stack>
              ) : (
                <Box
                  sx={{
                    borderRadius: 2,
                    border: '1px dashed',
                    borderColor: 'divider',
                    backgroundColor: 'background.default',
                    px: 1.25,
                    py: 1.1,
                  }}
                >
                  <Stack spacing={0.8}>
                    <Typography variant="body2" color="text.secondary">
                      В этом объединении пока нет участников.
                    </Typography>
                  </Stack>
                </Box>
              )}
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setActiveUnitDetailsId(null)}>Закрыть</Button>
          </DialogActions>
        </Dialog>

        <Dialog open={isMemberDialogOpen} onClose={closeMemberDialog} maxWidth="sm" fullWidth>
          <DialogTitle>Добавить участника</DialogTitle>
          <DialogContent dividers>
            <Stack spacing={1.25}>
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

