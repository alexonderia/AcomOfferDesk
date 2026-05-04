import { Navigate } from 'react-router-dom';
import { useAuth } from '@app/providers/AuthProvider';
import { hasAnyPermission } from '@shared/auth/permissions';
import { getDefaultPathByRole } from '@shared/lib/routing/getDefaultPathByRole';

type RoleRouteProps = {
  allowedRoles?: number[];
  allowedPermissions?: string[];
  children: JSX.Element;
};

export const RoleRoute = ({ allowedRoles = [], allowedPermissions = [], children }: RoleRouteProps) => {
  const { session } = useAuth();

  if (!session) {
    return <Navigate to="/login" replace />;
  }

  if (!session.businessAccess) {
    return <Navigate to="/account" replace />;
  }

  const isRoleAllowed = allowedRoles.length > 0 && allowedRoles.includes(session.roleId);
  const isPermissionAllowed = allowedPermissions.length > 0 && hasAnyPermission(session, allowedPermissions);

  if (!isRoleAllowed && !isPermissionAllowed) {
    return <Navigate to={getDefaultPathByRole(session.roleId, session.permissions)} replace />;
  }

  return children;
};
