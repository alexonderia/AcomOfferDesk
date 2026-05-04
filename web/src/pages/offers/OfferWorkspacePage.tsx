import { Navigate } from 'react-router-dom';
import { useAuth } from '@app/providers/AuthProvider';
import { OfferWorkspaceView } from '@features/offer-workspace';
import { hasPermission } from '@shared/auth/permissions';

export const OfferWorkspacePage = () => {
  const { session } = useAuth();
  if (!hasPermission(session, 'offers.workspace.read')) {
    return <Navigate to="/requests" replace />;
  }
  return <OfferWorkspaceView />;
};
