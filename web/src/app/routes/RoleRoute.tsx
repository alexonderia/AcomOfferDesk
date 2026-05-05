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

  const requiresPermission = allowedPermissions.length > 0;
  const isPermissionAllowed = !requiresPermission || hasAnyPermission(session, allowedPermissions);
  // Roles are UX-only fallback; protected access should be permission-based.
  const isRoleAllowed = allowedRoles.length === 0 || allowedRoles.includes(session.roleId);

  if (!isPermissionAllowed || (!requiresPermission && !isRoleAllowed)) {
    return <Navigate to={getDefaultPathByRole(session.roleId, session.permissions)} replace />;
  }

  return children;
};
