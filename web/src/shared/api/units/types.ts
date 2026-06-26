export type UnitActions = {
  can_create_child: boolean;
  can_update: boolean;
  can_delete: boolean;
  can_manage_members: boolean;
};

export type UnitMember = {
  user_id: string;
  full_name: string | null;
  role_id: number;
  role_name: string;
  status: string;
  id_parent_user: string | null;
};

export type AvailableUnitUser = {
  user_id: string;
  full_name: string | null;
  role_id: number;
  role_name: string;
  status: string;
};

export type UnitNode = {
  unit_id: number;
  name: string;
  id_parent: number | null;
  is_active: boolean;
  members: UnitMember[];
  children: UnitNode[];
  actions: {
    canCreateChild: boolean;
    canUpdate: boolean;
    canDelete: boolean;
    canManageMembers: boolean;
  };
};

export type RecommendedHierarchyNode = {
  user_id: string;
  full_name: string | null;
  role_id: number;
  role_name: string;
  status: string;
  id_parent_user: string | null;
  children: RecommendedHierarchyNode[];
};

type UnitMemberRow = Partial<UnitMember>;
type UnitNodeRow = {
  unit_id?: number;
  name?: string;
  id_parent?: number | null;
  is_active?: boolean;
  members?: UnitMemberRow[];
  children?: UnitNodeRow[];
  actions?: Partial<UnitActions>;
};

type AvailableUnitUserRow = Partial<AvailableUnitUser>;
type RecommendedHierarchyNodeRow = Partial<Omit<RecommendedHierarchyNode, 'children'>> & {
  children?: RecommendedHierarchyNodeRow[];
};

const normalizeMember = (item: UnitMemberRow): UnitMember => ({
  user_id: item.user_id ?? '',
  full_name: item.full_name ?? null,
  role_id: item.role_id ?? 0,
  role_name: item.role_name ?? '',
  status: item.status ?? 'review',
  id_parent_user: item.id_parent_user ?? null,
});

const normalizeActions = (actions?: Partial<UnitActions>) => ({
  canCreateChild: Boolean(actions?.can_create_child),
  canUpdate: Boolean(actions?.can_update),
  canDelete: Boolean(actions?.can_delete),
  canManageMembers: Boolean(actions?.can_manage_members),
});

export const normalizeUnitNode = (item: UnitNodeRow): UnitNode => ({
  unit_id: item.unit_id ?? 0,
  name: item.name ?? '',
  id_parent: item.id_parent ?? null,
  is_active: item.is_active ?? true,
  members: (item.members ?? []).map(normalizeMember),
  children: (item.children ?? []).map(normalizeUnitNode),
  actions: normalizeActions(item.actions),
});

export const normalizeAvailableUnitUser = (item: AvailableUnitUserRow): AvailableUnitUser => ({
  user_id: item.user_id ?? '',
  full_name: item.full_name ?? null,
  role_id: item.role_id ?? 0,
  role_name: item.role_name ?? '',
  status: item.status ?? 'review',
});

export const normalizeRecommendedHierarchyNode = (item: RecommendedHierarchyNodeRow): RecommendedHierarchyNode => ({
  user_id: item.user_id ?? '',
  full_name: item.full_name ?? null,
  role_id: item.role_id ?? 0,
  role_name: item.role_name ?? '',
  status: item.status ?? 'review',
  id_parent_user: item.id_parent_user ?? null,
  children: (item.children ?? []).map(normalizeRecommendedHierarchyNode),
});
