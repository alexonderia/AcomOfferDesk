import { getDefaultPathByRole } from '@shared/lib/routing/getDefaultPathByRole';

type SessionPathInput = {
  roleId: number;
  permissions: string[];
};

/**
 * Post-login navigation target. Always pass session.permissions into getDefaultPathByRole
 * (AuthCallbackPage, AuthPage, AccountStatePage must use this helper).
 */
export const resolveAuthenticatedPath = (nextPath: string, session: SessionPathInput): string => {
  if (nextPath !== '/') {
    return nextPath;
  }
  return getDefaultPathByRole(session.roleId, session.permissions);
};
