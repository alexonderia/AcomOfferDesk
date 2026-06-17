import { ROLE } from '@shared/constants/roles';
import { roleByTab, type UserTab } from './constants';

export const resolveUserTabFromParam = (value: string | null): UserTab => {
  if (
    value === 'economists' ||
    value === 'admins' ||
    value === 'security_officers' ||
    value === 'lead_economists' ||
    value === 'project_managers' ||
    value === 'operators'
  ) {
    return value;
  }
  return 'contractors';
};

const normalizeActionHref = (href: string) => {
  const normalizedHref = href.trim();
  if (!normalizedHref) return '';

  const url = normalizedHref.startsWith('http')
    ? new URL(normalizedHref)
    : new URL(normalizedHref, 'http://local');

  return url.pathname.replace(/\/{2,}/g, '/').replace(/\/$/, '');
};

export const canPatchUserStatus = (href: string, method: string) => {
  if (method.trim().toUpperCase() !== 'PATCH') return false;
  return /^\/api\/v1\/users\/(\{user_id\}|[^/]+)\/status$/.test(normalizeActionHref(href));
};

export const canPatchUserRole = (href: string, method: string) => {
  if (method.trim().toUpperCase() !== 'PATCH') return false;
  return /^\/api\/v1\/users\/(\{user_id\}|[^/]+)\/role$/.test(normalizeActionHref(href));
};

type GetScopedCreateRoleIdsParams = {
  activeTab: UserTab;
  availableRoleIds: number[];
  sessionRoleId: number | undefined;
};

export const getScopedCreateRoleIds = ({
  activeTab,
  availableRoleIds,
  sessionRoleId
}: GetScopedCreateRoleIdsParams) => {
  const uniqueRoleIds = Array.from(new Set(availableRoleIds));
  if (sessionRoleId !== ROLE.SUPERADMIN) {
    const scopedRoleIds = activeTab === 'contractors'
      ? uniqueRoleIds.filter((roleId) => roleId === ROLE.CONTRACTOR)
      : uniqueRoleIds.filter((roleId) => roleId !== ROLE.CONTRACTOR);
    return scopedRoleIds;
  }

  const preferredRoleId = roleByTab[activeTab];
  if (!uniqueRoleIds.includes(preferredRoleId)) {
    return uniqueRoleIds;
  }

  return [
    preferredRoleId,
    ...uniqueRoleIds.filter((roleId) => roleId !== preferredRoleId)
  ];
};
