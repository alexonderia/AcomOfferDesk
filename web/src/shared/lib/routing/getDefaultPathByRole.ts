import { ROLE } from '@shared/constants/roles';

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

  if (roleId === ROLE.PROJECT_MANAGER || roleId === ROLE.LEAD_ECONOMIST) {
    return '/pm-dashboard';
  }

  return '/requests';
};
