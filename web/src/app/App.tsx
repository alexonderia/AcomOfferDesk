import { useLocation } from 'react-router-dom';
import type { Location } from 'react-router-dom';
import { useAuth } from '@app/providers/AuthProvider';
import { AppRoutes } from '@app/routes/AppRoutes';
import { getDefaultPathByRole } from '@shared/lib/routing/getDefaultPathByRole';

export const App = () => {
  const { session } = useAuth();
  const location = useLocation();
  const state = location.state as { backgroundLocation?: Location } | null;

  const defaultPath = session ? (session.businessAccess ? getDefaultPathByRole(session.roleId) : '/account') : '/requests';

  return (
    <AppRoutes
      defaultPath={defaultPath}
      hasSession={Boolean(session)}
      location={location}
      backgroundLocation={state?.backgroundLocation}
    />
  );
};
