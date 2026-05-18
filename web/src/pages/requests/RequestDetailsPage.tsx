import { Navigate } from 'react-router-dom';
import { useAuth } from '@app/providers/AuthProvider';
import { RequestDetailsView } from '@features/request-details';
import { hasPermission } from '@shared/auth/permissions';

export const RequestDetailsPage = () => {
  const { session } = useAuth();
  if (!hasPermission(session, 'requests.read')) {
    return <Navigate to="/requests" replace />;
  }
  return <RequestDetailsView />;
};
