import { fetchJson } from '../client';

export type HierarchyUserBrief = {
  userId: string;
  fullName: string | null;
  roleId: number;
  roleName: string;
  status: string;
};

export type HierarchyUnitBrief = {
  unitId: number;
  name: string;
  parentUnitId: number | null;
};

export type HierarchyRelationBrief = HierarchyUserBrief & {
  sourceUnitId: number;
  sourceUnitName: string;
};

export type LegacyHierarchyState = {
  legacyManager: HierarchyUserBrief | null;
  legacySubordinates: HierarchyUserBrief[];
  isBusinessSource: boolean;
  note: string;
};

export type UserHierarchy = {
  user: HierarchyUserBrief;
  units: HierarchyUnitBrief[];
  managers: HierarchyRelationBrief[];
  subordinates: HierarchyRelationBrief[];
  legacyHierarchy: LegacyHierarchyState;
};

type HierarchyUserBriefPayload = {
  user_id: string;
  full_name?: string | null;
  role_id: number;
  role_name: string;
  status: string;
};

type HierarchyUnitBriefPayload = {
  unit_id: number;
  name: string;
  id_parent?: number | null;
};

type HierarchyRelationBriefPayload = HierarchyUserBriefPayload & {
  source_unit_id: number;
  source_unit_name: string;
};

type UserHierarchyPayload = {
  user: HierarchyUserBriefPayload;
  units?: HierarchyUnitBriefPayload[];
  managers?: HierarchyRelationBriefPayload[];
  subordinates?: HierarchyRelationBriefPayload[];
  legacy_hierarchy: {
    legacy_manager?: HierarchyUserBriefPayload | null;
    legacy_subordinates?: HierarchyUserBriefPayload[];
    is_business_source?: boolean;
    note: string;
  };
};

type UserHierarchyResponse = {
  data: UserHierarchyPayload;
};

const mapUserBrief = (item: HierarchyUserBriefPayload): HierarchyUserBrief => ({
  userId: item.user_id,
  fullName: item.full_name ?? null,
  roleId: item.role_id,
  roleName: item.role_name,
  status: item.status,
});

const mapRelationBrief = (item: HierarchyRelationBriefPayload): HierarchyRelationBrief => ({
  ...mapUserBrief(item),
  sourceUnitId: item.source_unit_id,
  sourceUnitName: item.source_unit_name,
});

const mapHierarchy = (response: UserHierarchyResponse): UserHierarchy => ({
  user: mapUserBrief(response.data.user),
  units: (response.data.units ?? []).map((unit) => ({
    unitId: unit.unit_id,
    name: unit.name,
    parentUnitId: unit.id_parent ?? null,
  })),
  managers: (response.data.managers ?? []).map(mapRelationBrief),
  subordinates: (response.data.subordinates ?? []).map(mapRelationBrief),
  legacyHierarchy: {
    legacyManager: response.data.legacy_hierarchy.legacy_manager
      ? mapUserBrief(response.data.legacy_hierarchy.legacy_manager)
      : null,
    legacySubordinates: (response.data.legacy_hierarchy.legacy_subordinates ?? []).map(mapUserBrief),
    isBusinessSource: Boolean(response.data.legacy_hierarchy.is_business_source),
    note: response.data.legacy_hierarchy.note,
  },
});

export const getMyHierarchy = async (): Promise<UserHierarchy> => {
  const response = await fetchJson<UserHierarchyResponse>(
    '/api/v1/users/me/hierarchy',
    { method: 'GET' },
    'Ошибка загрузки вашей иерархии'
  );

  return mapHierarchy(response);
};

export const getUserHierarchy = async (userId: string): Promise<UserHierarchy> => {
  const response = await fetchJson<UserHierarchyResponse>(
    `/api/v1/users/${userId}/hierarchy`,
    { method: 'GET' },
    'Ошибка загрузки иерархии сотрудника'
  );

  return mapHierarchy(response);
};
