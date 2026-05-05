import type { PlanDashboardSummary, PlanRequestStats, PlanTreeNode } from '@shared/api/plans';

export const ALL_SUBORDINATES_SCOPE = '__all_descendants__';

export type SubordinateFilterOption = {
  userId: string;
  label: string;
};

export type PlanDistributionItem = {
  key: string;
  planId: number | null;
  label: string;
  amount: number;
  percent: number;
  planAmount: number;
  factAmount: number;
  progressPercent: number;
  color: string;
};

export type PlanFilterOption = {
  planId: number;
  label: string;
};

export type PlanExecutionSlice = {
  key: string;
  planId: number;
  label: string;
  value: number;
  planAmount: number;
  factAmount: number;
  progressPercent: number;
  color: string;
};

export type PlanRequestFactMetrics = {
  totalRequests?: number | null;
  distributedRequests?: number | null;
  requestFactAmount?: number | null;
  periodFactAmount?: number | null;
  completionPercent?: number | null;
  periodCompletionPercent?: number | null;
  unallocatedRequests?: number | null;
  unallocatedAmount?: number | null;
};

export type PlanSideSummaryData = {
  personalProgressPercent?: number | null;
  personalFactAmount?: number | null;
  personalPlanAmount?: number | null;
  personalInProgressRequestsCount?: number | null;
  directSubordinates?: Array<{
    userId: string;
    userName: string;
    userRole: string;
    factAmount: number;
    planAmount: number;
    progressPercent: number;
    inProgressRequestsCount: number;
  }>;
};

const distributionPalette = ['#3b82f6', '#f59e0b', '#34c759', '#8b5cf6', '#06b6d4'];

const toPercent = (fact: number, plan: number) => (plan > 0 ? (fact / plan) * 100 : 0);

export const formatPercent = (value: number) => `${Number.isFinite(value) ? value.toFixed(2) : '0.00'}%`;

export const periodToDate = (period: string) => `${period}-01`;

export const formatPeriodLabel = (period: string) => {
  const date = new Date(`${period}-01T00:00:00`);
  if (Number.isNaN(date.getTime())) {
    return period;
  }
  const formatted = new Intl.DateTimeFormat('ru-RU', { month: 'long', year: 'numeric' }).format(date);
  return formatted.charAt(0).toUpperCase() + formatted.slice(1);
};

export const getInitials = (value: string) => {
  const parts = value
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (parts.length === 0) {
    return '—';
  }
  return parts
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join('');
};

export const flattenPlanNodes = (nodes: PlanTreeNode[]): PlanTreeNode[] => {
  const result: PlanTreeNode[] = [];
  const walk = (node: PlanTreeNode) => {
    result.push(node);
    node.children.forEach(walk);
  };
  nodes.forEach(walk);
  return result;
};

export const findPlanNodeByPlanId = (nodes: PlanTreeNode[], planId: number): PlanTreeNode | null => {
  for (const node of nodes) {
    if (node.plan_id === planId) {
      return node;
    }
    const fromChild = findPlanNodeByPlanId(node.children, planId);
    if (fromChild) {
      return fromChild;
    }
  }
  return null;
};

const mergeActionFlags = (left: PlanTreeNode['available_actions'], right: PlanTreeNode['available_actions']) => ({
  create_child_plan: left.create_child_plan || right.create_child_plan,
  create_subplan: left.create_subplan || right.create_subplan,
  delegate_plan: left.delegate_plan || right.delegate_plan,
  edit_plan: left.edit_plan || right.edit_plan,
  delete_child_plan: left.delete_child_plan || right.delete_child_plan,
  activate_plan: left.activate_plan || right.activate_plan,
  close_plan: left.close_plan || right.close_plan,
  view_plan: left.view_plan || right.view_plan,
});

const normalizePresentationNode = (node: PlanTreeNode): PlanTreeNode => {
  const normalizedChildren = node.children.map(normalizePresentationNode);

  if (
    normalizedChildren.length === 1
    && normalizedChildren[0].user_id === node.user_id
    && node.personal_plan_amount <= 0
    && node.fact_amount_self <= 0
  ) {
    const repeatedChild = normalizedChildren[0];
    return {
      ...repeatedChild,
      available_actions: mergeActionFlags(node.available_actions, repeatedChild.available_actions),
      plan_name: node.plan_name,
      plan_amount: node.plan_amount,
      delegated_amount: node.delegated_amount,
      personal_plan_amount: node.personal_plan_amount,
      unallocated_amount: node.unallocated_amount,
      fact_amount_self: node.fact_amount_self,
      fact_amount_subtree: node.fact_amount_subtree,
      remaining_amount: node.remaining_amount,
      progress_percent: node.progress_percent,
    };
  }

  return {
    ...node,
    children: normalizedChildren,
  };
};

export const normalizePlanTreesForPresentation = (trees: PlanTreeNode[]) => trees.map(normalizePresentationNode);

export const collectSubordinateOptions = (nodes: PlanTreeNode[]): SubordinateFilterOption[] => {
  const labelsByUserId = new Map<string, string>();

  flattenPlanNodes(nodes).forEach((node) => {
    if (!labelsByUserId.has(node.user_id)) {
      labelsByUserId.set(node.user_id, `${node.user_name} (${node.user_role})`);
    }
  });

  return Array.from(labelsByUserId.entries())
    .map(([userId, label]) => ({ userId, label }))
    .sort((left, right) => left.label.localeCompare(right.label, 'ru'));
};

export const findSubtreeByUserId = (node: PlanTreeNode, userId: string): PlanTreeNode | null => {
  if (node.user_id === userId) {
    return node;
  }
  for (const child of node.children) {
    const found = findSubtreeByUserId(child, userId);
    if (found) {
      return found;
    }
  }
  return null;
};

export const deriveSummaryFromTrees = (trees: PlanTreeNode[]): PlanDashboardSummary => {
  const totalPlanAmount = trees.reduce((sum, node) => sum + node.plan_amount, 0);
  const totalFactAmount = trees.reduce((sum, node) => sum + node.fact_amount_subtree, 0);
  const totalPeriodFactAmount = trees.reduce((sum, node) => sum + (node.period_fact_amount ?? 0), 0);
  const totalRemainingAmount = trees.reduce((sum, node) => sum + node.remaining_amount, 0);

  return {
    total_plan_amount: totalPlanAmount,
    total_fact_amount: totalFactAmount,
    total_period_fact_amount: totalPeriodFactAmount,
    total_remaining_amount: totalRemainingAmount,
    total_progress_percent: toPercent(totalFactAmount, totalPlanAmount),
    total_period_progress_percent: toPercent(totalPeriodFactAmount, totalPlanAmount),
  };
};

export const countUniqueParticipants = (trees: PlanTreeNode[]) =>
  new Set(flattenPlanNodes(trees).map((node) => node.user_id)).size;

export const getExpandableNodeIds = (trees: PlanTreeNode[]) =>
  flattenPlanNodes(trees)
    .filter((node) => node.children.length > 0)
    .map((node) => node.plan_id);

export const filterPlanTree = (node: PlanTreeNode, query: string): PlanTreeNode | null => {
  const normalizedQuery = query.trim().toLowerCase();
  if (!normalizedQuery) {
    return node;
  }

  const matchedChildren = node.children
    .map((child) => filterPlanTree(child, normalizedQuery))
    .filter((child): child is PlanTreeNode => child !== null);

  const selfMatches = [node.plan_name, node.user_name, node.user_role].some((value) =>
    value.toLowerCase().includes(normalizedQuery)
  );

  if (selfMatches || matchedChildren.length > 0) {
    return {
      ...node,
      children: matchedChildren,
    };
  }

  return null;
};

export const buildDistributionItems = (trees: PlanTreeNode[]): PlanDistributionItem[] => {
  const baseNodes = trees.flatMap((node) => (node.children.length > 0 ? node.children : [node]));
  const total = baseNodes.reduce((sum, node) => sum + node.plan_amount, 0);

  if (baseNodes.length === 0 || total <= 0) {
    return [];
  }

  const sorted = [...baseNodes].sort((left, right) => right.plan_amount - left.plan_amount);
  const leadingItems: PlanDistributionItem[] = sorted.slice(0, 4).map((node, index) => ({
    key: String(node.plan_id),
    planId: node.plan_id,
    label: `${node.plan_name} (${node.user_name})`,
    amount: node.plan_amount,
    percent: toPercent(node.plan_amount, total),
    planAmount: node.plan_amount,
    factAmount: node.fact_amount_subtree,
    progressPercent: Math.max(0, Math.min(100, toPercent(node.fact_amount_subtree, node.plan_amount))),
    color: distributionPalette[index % distributionPalette.length],
  }));

  const remainingAmount = sorted.slice(4).reduce((sum, node) => sum + node.plan_amount, 0);
  if (remainingAmount > 0) {
    leadingItems.push({
      key: 'other',
      planId: null,
      label: 'Другие',
      amount: remainingAmount,
      percent: toPercent(remainingAmount, total),
      planAmount: remainingAmount,
      factAmount: sorted.slice(4).reduce((sum, node) => sum + node.fact_amount_subtree, 0),
      progressPercent: Math.max(
        0,
        Math.min(
          100,
          toPercent(
            sorted.slice(4).reduce((sum, node) => sum + node.fact_amount_subtree, 0),
            remainingAmount
          )
        )
      ),
      color: '#cbd5e1',
    });
  }

  return leadingItems;
};

export const buildRequestFactMetrics = (
  summary: PlanDashboardSummary | null,
  requestStats?: PlanRequestStats | null,
  periodFactAmount?: number | null,
  periodCompletionPercent?: number | null
): PlanRequestFactMetrics => ({
  totalRequests: requestStats?.total_requests ?? null,
  distributedRequests: requestStats?.distributed_requests ?? null,
  requestFactAmount: requestStats?.request_fact_amount ?? summary?.total_fact_amount ?? 0,
  periodFactAmount: periodFactAmount ?? summary?.total_period_fact_amount ?? 0,
  completionPercent: requestStats?.completion_percent ?? summary?.total_progress_percent ?? 0,
  periodCompletionPercent: periodCompletionPercent ?? summary?.total_period_progress_percent ?? 0,
  unallocatedRequests: requestStats?.unallocated_requests ?? null,
  unallocatedAmount: requestStats?.unallocated_amount ?? null,
});

export const buildSideSummaryData = (trees: PlanTreeNode[], currentUserId: string | null): PlanSideSummaryData => {
  const allNodes = flattenPlanNodes(trees);
  const currentNode = (currentUserId ? allNodes.find((node) => node.user_id === currentUserId) : null) ?? trees[0] ?? null;

  if (!currentNode) {
    return {};
  }

  const personalPlanAmount = currentNode.personal_plan_amount > 0 ? currentNode.personal_plan_amount : currentNode.plan_amount;
  const personalFactAmount = currentNode.fact_amount_self;
  const personalProgressPercent = toPercent(personalFactAmount, personalPlanAmount);
  const managerUserId = currentUserId ?? currentNode.user_id;

  const personalInProgressRequestsCount = currentNode.in_progress_requests_count ?? 0;
  const directSubordinateNodes = allNodes.filter(
    (node) =>
      node.parent_user_id_snapshot === managerUserId
      && node.user_id !== managerUserId,
  );
  const directSubordinatesMap = new Map<
    string,
    {
      userId: string;
      userName: string;
      userRole: string;
      factAmount: number;
      planAmount: number;
      inProgressRequestsCount: number;
    }
  >();
  directSubordinateNodes.forEach((node) => {
    const existing = directSubordinatesMap.get(node.user_id);
    if (!existing) {
      directSubordinatesMap.set(node.user_id, {
        userId: node.user_id,
        userName: node.user_name,
        userRole: node.user_role,
        factAmount: node.fact_amount_subtree,
        planAmount: node.plan_amount,
        // Count is employee-level; avoid summing duplicates from multiple nodes/subplans.
        inProgressRequestsCount: node.in_progress_requests_count ?? 0,
      });
      return;
    }
    existing.factAmount += node.fact_amount_subtree;
    existing.planAmount += node.plan_amount;
  });
  const directSubordinates = Array.from(directSubordinatesMap.values())
    .map((item) => ({
      ...item,
      progressPercent: toPercent(item.factAmount, item.planAmount),
    }))
    .sort((left, right) => left.userName.localeCompare(right.userName, 'ru'));

  return {
    personalProgressPercent,
    personalFactAmount,
    personalPlanAmount,
    personalInProgressRequestsCount,
    directSubordinates,
  };
};

export const buildPlanFilterOptions = (trees: PlanTreeNode[]): PlanFilterOption[] =>
  flattenPlanNodes(trees)
    .map((node) => ({
      planId: node.plan_id,
      label: `${node.plan_name} (${node.user_name})`,
    }))
    .sort((left, right) => left.label.localeCompare(right.label, 'ru'));

export const buildExecutionSlices = (trees: PlanTreeNode[]): PlanExecutionSlice[] => {
  const baseNodes = trees.flatMap((node) => (node.children.length > 0 ? node.children : [node]));
  const totalFact = baseNodes.reduce((sum, node) => sum + Math.max(node.fact_amount_subtree, 0), 0);
  const totalPlan = baseNodes.reduce((sum, node) => sum + Math.max(node.plan_amount, 0), 0);
  const denominator = totalFact > 0 ? totalFact : totalPlan;

  if (denominator <= 0) {
    return [];
  }

  return baseNodes.map((node, index) => {
    const value = totalFact > 0 ? Math.max(node.fact_amount_subtree, 0) : Math.max(node.plan_amount, 0);
    return {
      key: String(node.plan_id),
      planId: node.plan_id,
      label: `${node.plan_name} (${node.user_name})`,
      value,
      planAmount: node.plan_amount,
      factAmount: node.fact_amount_subtree,
      progressPercent: Math.max(0, Math.min(100, toPercent(node.fact_amount_subtree, node.plan_amount))),
      color: distributionPalette[index % distributionPalette.length],
    };
  });
};
