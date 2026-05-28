import { useLocation } from 'react-router-dom';
import type { Location } from 'react-router-dom';
import { useAuth } from '@app/providers/AuthProvider';
import { RealtimeProvider } from '@app/providers/RealtimeProvider';
import { AppRoutes } from '@app/routes/AppRoutes';
import { NotificationsProvider, NotificationsPushLayer } from '@features/notifications';
import { getDefaultPathByRole } from '@shared/lib/routing/getDefaultPathByRole';
import { SnackbarProvider } from 'notistack';
import { NOTIFICATION_PUSH_MAX_SNACK } from '@features/notifications/model/constants';

export const App = () => {
  const { session } = useAuth();
  const location = useLocation();
  const state = location.state as { backgroundLocation?: Location } | null;

  const defaultPath = session
    ? (session.businessAccess ? getDefaultPathByRole(session.roleId, session.permissions) : '/account')
    : '/requests';

  return (
    <NotificationsProvider>
      <RealtimeProvider>
        <SnackbarProvider
          maxSnack={NOTIFICATION_PUSH_MAX_SNACK}
          autoHideDuration={10_000}
          preventDuplicate
          dense
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        >
          <NotificationsPushLayer />
          <AppRoutes
            defaultPath={defaultPath}
            hasSession={Boolean(session)}
            location={location}
            backgroundLocation={state?.backgroundLocation}
          />
        </SnackbarProvider>
      </RealtimeProvider>
    </NotificationsProvider>
  );
};
