import { Navigate } from 'react-router-dom';
import { useAuth } from '@app/providers/AuthProvider';
import { NormativeFilesPageView } from '@features/normative-files';
import { hasPermission } from '@shared/auth/permissions';

export const NormativeFilesPage = () => {
  const { session } = useAuth();
  const canManageNormativeFiles = hasPermission(session, 'normative_files.manage');

  if (!canManageNormativeFiles) {
    return <Navigate to="/requests" replace />;
  }

  return <NormativeFilesPageView />;
};
