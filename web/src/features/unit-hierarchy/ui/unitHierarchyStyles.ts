import { alpha } from '@mui/material/styles';
import type { UnitMember } from '@shared/api/units';
import { ROLE } from '@shared/constants/roles';

export const hierarchyPageColors = {
  canvas: '#f8fafc',
  canvasBorder: '#dbe3ec',
  cardBorder: '#d3dce6',
  connector: '#7a90ab',
  shadow: '0 2px 8px rgba(15, 23, 42, 0.06)',
  textPrimary: '#1f2937',
  textSecondary: '#6b7280',
  softBlue: '#2563eb',
  softPink: '#c45d86',
  softTeal: '#0f766e',
} as const;

export const hierarchyCanvasBackground = `
  linear-gradient(180deg, rgba(255, 255, 255, 1) 0%, rgba(255, 255, 255, 1) 100%)
`;

export const hierarchySurfaceBackground = `
  linear-gradient(180deg, rgba(255, 255, 255, 1) 0%, rgba(255, 255, 255, 1) 100%)
`;

export const sectionCardSx = {
  borderRadius: 2,
  borderColor: alpha(hierarchyPageColors.canvasBorder, 0.9),
  backgroundImage: 'none',
  backgroundColor: '#ffffff',
  boxShadow: '0 1px 2px rgba(15, 23, 42, 0.04)',
} as const;

export const connectorLineSx = {
  backgroundColor: hierarchyPageColors.connector,
  borderRadius: 999,
} as const;

export const outlinedIconButtonSx = {
  border: `1px solid ${alpha(hierarchyPageColors.softBlue, 0.45)}`,
  borderRadius: 1.5,
  color: hierarchyPageColors.softBlue,
  transition: 'border-color 0.16s ease, background-color 0.16s ease',
  '&:hover': {
    borderColor: hierarchyPageColors.softBlue,
    backgroundColor: alpha(hierarchyPageColors.softBlue, 0.08),
  },
} as const;

export const outlinedActionButtonSx = {
  minHeight: 42,
  borderRadius: 1.75,
  px: 2,
  fontSize: 14,
  fontWeight: 600,
  borderColor: alpha(hierarchyPageColors.softBlue, 0.45),
  color: hierarchyPageColors.softBlue,
  backgroundColor: '#ffffff',
  transition: 'border-color 0.16s ease, background-color 0.16s ease',
  '&:hover': {
    borderColor: hierarchyPageColors.softBlue,
    backgroundColor: alpha(hierarchyPageColors.softBlue, 0.08),
  },
} as const;

export const outlinedActionIconButtonSx = {
  ...outlinedIconButtonSx,
  width: 42,
  height: 42,
  borderRadius: 1.75,
} as const;

export const orgNodeLayout = {
  cardWidth: 332,
  childGap: 26,
  connectorHeight: 20,
} as const;

export const orgNodeCardSx = {
  width: orgNodeLayout.cardWidth,
  maxWidth: `min(${orgNodeLayout.cardWidth}px, calc(100vw - 40px))`,
  borderRadius: 2.5,
  border: `1px solid ${alpha(hierarchyPageColors.cardBorder, 0.98)}`,
  backgroundColor: '#ffffff',
  boxShadow: hierarchyPageColors.shadow,
  px: 1.4,
  py: 1.3,
  zIndex: 1,
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
  return 'Подраздел';
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
