import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '@app/providers/AuthProvider';

export const ProtectedRoute = () => {
  const { isAuthenticated, status, session } = useAuth();
  const location = useLocation();

  if (status === 'authenticating') {
    return null;
  }

  if (!session || !isAuthenticated) {
    const next = location.pathname !== '/' ? `?next=${encodeURIComponent(location.pathname + location.search)}` : '';
    return <Navigate to={`/login${next}`} replace />;
  }

  if (session && !session.businessAccess && location.pathname !== '/account') {
    return <Navigate to="/account" replace />;
  }

  return <Outlet />;
};
