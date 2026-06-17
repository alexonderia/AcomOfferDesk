import { ROLE } from '@shared/constants/roles';

/** Permissions that allow opening the requests list or contractor request tabs. */
export const REQUESTS_ROUTE_PERMISSIONS = [
  'requests.read',
  'department.requests.read',
  'requests.open.read',
  'requests.offered.read',
] as const;

const canOpenRequestsArea = (permissions: string[]) =>
  REQUESTS_ROUTE_PERMISSIONS.some((permission) => permissions.includes(permission));

export const getDefaultPathByRole = (roleId: number, permissions: string[] = []) => {
  if (permissions.includes('dashboard.process.read') || permissions.includes('department.dashboard.read')) {
    return '/pm-dashboard';
  }

  if (permissions.includes('dashboard.savings.read') || permissions.includes('department.dashboard.read')) {
    return '/pm-dashboard/savings';
  }

  if (
    permissions.includes('dashboard.plans.read')
    || permissions.includes('department.plans.read')
    || permissions.includes('department.plans.manage')
  ) {
    return '/pm-dashboard/plan';
  }

  if (permissions.includes('users.read')) {
    return '/admin';
  }

  if (permissions.includes('contractors.read')) {
    return '/contractors';
  }

  if (roleId === ROLE.PROJECT_MANAGER || roleId === ROLE.LEAD_ECONOMIST) {
    return '/pm-dashboard';
  }

  if (canOpenRequestsArea(permissions)) {
    return '/requests';
  }

  return '/account';
};
