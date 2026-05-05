import { Navigate } from 'react-router-dom';
import { useAuth } from '@app/providers/AuthProvider';
import { ROLE } from '@shared/constants/roles';

type RoleRouteProps = {
  allowedRoles: number[];
  children: JSX.Element;
};

const getDefaultPath = (roleId?: number | null) => {
  if (roleId === ROLE.PROJECT_MANAGER || roleId === ROLE.LEAD_ECONOMIST) {
    return '/pm-dashboard';
  }

  if (roleId === ROLE.SUPERADMIN || roleId === ROLE.ADMIN) {
    return '/admin';
  }
  return '/requests';
};

export const RoleRoute = ({ allowedRoles, children }: RoleRouteProps) => {
  const { session } = useAuth();

  if (!session) {
    return <Navigate to="/login" replace />;
  }

  if (!session.businessAccess) {
    return <Navigate to="/account" replace />;
  }

  if (!allowedRoles.includes(session.roleId)) {
    return <Navigate to={getDefaultPath(session.roleId)} replace />;
  }

  return children;
};
