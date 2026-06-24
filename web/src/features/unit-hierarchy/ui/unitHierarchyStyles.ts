import { alpha } from '@mui/material/styles';
import type { UnitMember } from '@shared/api/units';
import { ROLE } from '@shared/constants/roles';

export const hierarchyPageColors = {
  canvas: '#f4f8fc',
  canvasBorder: '#d9e4ef',
  cardBorder: '#cfdae7',
  connector: '#5d95c6',
  shadow: '0 18px 36px rgba(15, 23, 42, 0.08)',
  textPrimary: '#17263d',
  textSecondary: '#6d8094',
  softBlue: '#2f78d8',
  softPink: '#cc6d90',
  softTeal: '#309d91',
} as const;

export const hierarchyCanvasBackground = `
  radial-gradient(circle at top left, ${alpha(hierarchyPageColors.softBlue, 0.14)} 0, transparent 28%),
  radial-gradient(circle at top right, ${alpha(hierarchyPageColors.softTeal, 0.12)} 0, transparent 24%),
  linear-gradient(180deg, rgba(255, 255, 255, 0.96) 0%, rgba(244, 248, 252, 0.98) 100%)
`;

export const hierarchySurfaceBackground = `
  linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 251, 255, 0.96) 100%)
`;

export const sectionCardSx = {
  borderRadius: 3,
  borderColor: alpha(hierarchyPageColors.canvasBorder, 0.9),
  backgroundImage: hierarchySurfaceBackground,
  backgroundColor: '#ffffff',
  boxShadow: '0 12px 30px rgba(15, 23, 42, 0.05)',
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
