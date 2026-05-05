export type PlanNodeActions = {
  create_child_plan: boolean;
  create_subplan: boolean;
  delegate_plan: boolean;
  edit_plan: boolean;
  delete_child_plan: boolean;
  activate_plan: boolean;
  close_plan: boolean;
  view_plan: boolean;
};

export type PlanTreeNode = {
  plan_id: number;
  plan_name: string;
  id_parent_plan: number | null;
  user_id: string;
  user_name: string;
  user_role: string;
  parent_user_id_snapshot: string | null;
  period_start: string;
  period_end: string;
  plan_amount: number;
  delegated_amount: number;
  personal_plan_amount: number;
  unallocated_amount: number;
  fact_amount_self: number;
  fact_amount_subtree: number;
  period_fact_amount: number;
  period_progress_percent: number;
  in_progress_requests_count: number;
  remaining_amount: number;
  progress_percent: number;
  available_actions: PlanNodeActions;
  children: PlanTreeNode[];
};

export type PlanDashboardSummary = {
  total_plan_amount: number;
  total_fact_amount: number;
  total_period_fact_amount: number;
  total_remaining_amount: number;
  total_progress_percent: number;
  total_period_progress_percent: number;
};

export type PlanRequestStats = {
  total_requests: number;
  distributed_requests: number;
  unallocated_requests: number;
  request_fact_amount: number;
  unallocated_amount: number;
  completion_percent: number;
};

export type PlanDashboardData = {
  period: string;
  period_start: string;
  period_end: string;
  can_create_root_plan: boolean;
  root_plan_exists: boolean;
  summary: PlanDashboardSummary;
  request_stats: PlanRequestStats;
  tree: PlanTreeNode | null;
  trees: PlanTreeNode[];
};

export type PlanDashboardResult = PlanDashboardData;

export type PlanMutationResult = {
  plan_id: number;
  plan_name: string;
  id_parent_plan: number | null;
  user_id: string;
  parent_user_id_snapshot: string | null;
  period_start: string;
  period_end: string;
  plan_amount: number;
};

export type PlanDelegateCandidate = {
  user_id: string;
  full_name: string | null;
  role_name: string;
  has_plan_for_period: boolean;
  existing_plan_id: number | null;
};

export type PlanOption = {
  plan_id: number;
  plan_name: string;
  user_id: string;
  user_name: string;
  user_role: string;
  period_start: string;
  period_end: string;
  is_closed: boolean;
};
