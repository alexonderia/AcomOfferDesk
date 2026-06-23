import type { UnitMember } from '@shared/api/units';
import { ROLE } from '@shared/constants/roles';

export const hierarchyPageColors = {
  canvas: '#f8fafc',
  canvasBorder: '#e2e8f0',
  cardBorder: '#cfd6e3',
  connector: '#3a9cc7',
  shadow: '0 4px 12px rgba(27, 39, 57, 0.08)',
  textPrimary: '#172033',
  textSecondary: '#7a8699',
  softBlue: '#3f83f8',
  softPink: '#d36b97',
  softTeal: '#50a4a2',
} as const;

export const sectionCardSx = {
  borderRadius: 2,
  borderColor: 'divider',
  backgroundColor: 'background.paper',
  boxShadow: 'none',
} as const;

export const connectorLineSx = {
  backgroundColor: hierarchyPageColors.connector,
  borderRadius: 999,
} as const;

export const statusLabelByCode: Record<string, string> = {
  active: 'Активен',
  inactive: 'Неактивен',
  review: 'На проверке',
  blacklist: 'Заблокирован',
};

export const getUnitLevelLabel = (depth: number) => {
  if (depth === 0) {
    return 'Подразделение';
  }
  if (depth === 1) {
    return 'Проект';
  }
  return 'Модуль';
};

export const getMemberDisplayName = (member: Pick<UnitMember, 'full_name' | 'user_id'>) =>
  member.full_name?.trim() || member.user_id;

export const isPlaceholderPersonName = (value: string | null | undefined) => {
  const normalized = (value ?? '').trim().toLowerCase();
  return normalized.includes('вакан') || normalized.includes('не указано');
};

export const getMemberAccentColor = (roleName: string) => {
  const normalizedRole = roleName.trim().toLowerCase();
  if (normalizedRole.includes('админ')) {
    return '#1d4ed8';
  }
  if (normalizedRole.includes('ведущ')) {
    return '#0f766e';
  }
  if (normalizedRole.includes('руковод') || normalizedRole.includes('глав')) {
    return '#7c3aed';
  }
  if (normalizedRole.includes('контраг')) {
    return '#b45309';
  }
  return '#475569';
};

type MemberGroup = {
  contractors: UnitMember[];
  leaders: UnitMember[];
  team: UnitMember[];
};

const leaderRoleIds = new Set<number>([ROLE.SUPERADMIN, ROLE.ADMIN, ROLE.PROJECT_MANAGER, ROLE.LEAD_ECONOMIST]);
const contractorRoleIds = new Set<number>([ROLE.CONTRACTOR]);

const isLeaderRole = (member: UnitMember) => {
  const normalizedRole = member.role_name.trim().toLowerCase();
  return (
    leaderRoleIds.has(member.role_id)
    || normalizedRole.includes('админ')
    || normalizedRole.includes('руковод')
    || normalizedRole.includes('ведущ')
    || normalizedRole.includes('глав')
  );
};

const isContractorRole = (member: UnitMember) => {
  const normalizedRole = member.role_name.trim().toLowerCase();
  return contractorRoleIds.has(member.role_id) || normalizedRole.includes('контраг');
};

export const groupMembersForOrgChart = (members: UnitMember[]): MemberGroup => {
  const groups: MemberGroup = {
    leaders: [],
    team: [],
    contractors: [],
  };

  members.forEach((member) => {
    if (isContractorRole(member)) {
      groups.contractors.push(member);
      return;
    }

    if (isLeaderRole(member)) {
      groups.leaders.push(member);
      return;
    }

    groups.team.push(member);
  });

  return groups;
};
