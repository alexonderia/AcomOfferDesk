import { ROLE } from '@shared/constants/roles';

export const getDefaultPathByRole = (roleId: number) =>
  roleId === ROLE.PROJECT_MANAGER || roleId === ROLE.LEAD_ECONOMIST
    ? '/pm-dashboard'
    : roleId === ROLE.SUPERADMIN || roleId === ROLE.ADMIN
      ? '/admin'
      : '/requests';
