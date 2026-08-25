import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '@app/providers/AuthProvider';
import { TechnicalUnavailablePage } from '@pages/technical';

export const ProtectedRoute = () => {
  const { isAuthenticated, status, session } = useAuth();
  const location = useLocation();

  if (status === 'authenticating') {
    return null;
  }

  if (status === 'unavailable') {
    return <TechnicalUnavailablePage />;
  }

  if (!session || !isAuthenticated) {
    const next = location.pathname !== '/' ? `?next=${encodeURIComponent(location.pathname + location.search)}` : '';
    return <Navigate to={`/login${next}`} replace />;
  }

  if (session && !session.businessAccess && location.pathname !== '/account' && location.pathname !== '/profile/onboarding') {
    const onboardingPath = session.onboardingState === 'first_login' ? '/profile/onboarding' : '/account';
    return <Navigate to={onboardingPath} replace />;
  }
  if (session?.onboardingState === 'first_login' && session.businessAccess && location.pathname !== '/profile/onboarding' && location.pathname !== '/account') {
    return <Navigate to="/profile/onboarding" replace />;
  }

  return <Outlet />;
};
