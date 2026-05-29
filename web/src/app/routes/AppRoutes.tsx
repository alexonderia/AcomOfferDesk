import { Suspense, lazy } from 'react';
import { Box, CircularProgress } from '@mui/material';
import { Navigate, Route, Routes } from 'react-router-dom';
import type { Location } from 'react-router-dom';
import { AppLayout } from '@app/layouts/AppLayout';
import { ProtectedRoute } from '@app/routes/ProtectedRoute';
import { RoleRoute } from '@app/routes/RoleRoute';
import { REQUESTS_ROUTE_PERMISSIONS } from '@shared/lib/routing/getDefaultPathByRole';

const AuthPage = lazy(async () => ({ default: (await import('@pages/auth/AuthPage')).AuthPage }));
const AuthCallbackPage = lazy(async () => ({ default: (await import('@pages/auth/AuthCallbackPage')).AuthCallbackPage }));
const AccountStatePage = lazy(async () => ({ default: (await import('@pages/auth/AccountStatePage')).AccountStatePage }));
const RegistrationLinkStatusPage = lazy(
  async () => ({ default: (await import('@pages/auth/RegistrationLinkStatusPage')).RegistrationLinkStatusPage })
);
const VerifyEmailPage = lazy(async () => ({ default: (await import('@pages/auth/VerifyEmailPage')).VerifyEmailPage }));
const RequestsPage = lazy(async () => ({ default: (await import('@pages/requests/RequestsPage')).RequestsPage }));
const CreateRequestPage = lazy(async () => ({ default: (await import('@pages/requests/CreateRequestPage')).CreateRequestPage }));
const RequestDetailsPage = lazy(async () => ({ default: (await import('@pages/requests/RequestDetailsPage')).RequestDetailsPage }));
const ContractorRequestDetailsPage = lazy(
  async () => ({ default: (await import('@pages/requests/ContractorRequestDetailsPage')).ContractorRequestDetailsPage })
);
const OfferWorkspacePage = lazy(async () => ({ default: (await import('@pages/offers/OfferWorkspacePage')).OfferWorkspacePage }));
const AdminPage = lazy(async () => ({ default: (await import('@pages/admin/AdminPage')).AdminPage }));
const ContractorsPage = lazy(async () => ({ default: (await import('@pages/contractors/ContractorsPage')).ContractorsPage }));
const FeedbackPage = lazy(async () => ({ default: (await import('@pages/feedback/FeedbackPage')).FeedbackPage }));
const ProjectManagerDashboardPage = lazy(
  async () => ({ default: (await import('@pages/dashboard/ProjectManagerDashboardPage')).ProjectManagerDashboardPage })
);
const ProjectManagerSavingsPage = lazy(
  async () => ({ default: (await import('@pages/dashboard/ProjectManagerSavingsPage')).ProjectManagerSavingsPage })
);
const ProjectManagerPlanPage = lazy(
  async () => ({ default: (await import('@pages/dashboard/ProjectManagerPlanPage')).ProjectManagerPlanPage })
);

type AppRoutesProps = {
  defaultPath: string;
  hasSession: boolean;
  location: Location;
  backgroundLocation?: Location;
};

const RouteFallback = () => (
  <Box
    sx={{
      minHeight: '40vh',
      display: 'grid',
      placeItems: 'center'
    }}
  >
    <CircularProgress size={28} />
  </Box>
);

export const AppRoutes = ({ defaultPath, hasSession, location, backgroundLocation }: AppRoutesProps) => {
  return (
    <>
      <Suspense fallback={<RouteFallback />}>
        <Routes location={backgroundLocation ?? location}>
          <Route path="/login" element={<AuthPage />} />
          <Route path="/auth/login" element={<AuthPage />} />
          <Route path="/auth/callback" element={<AuthCallbackPage />} />
          <Route path="/auth/registration-link-status" element={<RegistrationLinkStatusPage />} />
          <Route path="/verify-email" element={<VerifyEmailPage />} />
          <Route element={<ProtectedRoute />}>
            <Route path="/account" element={<AccountStatePage />} />
            <Route element={<AppLayout />}>
              <Route path="/" element={<Navigate to={defaultPath} replace />} />
              <Route
                path="/requests"
                element={
                  <RoleRoute allowedPermissions={[...REQUESTS_ROUTE_PERMISSIONS]}>
                    <RequestsPage />
                  </RoleRoute>
                }
              />
              <Route
                path="/requests/create"
                element={
                  <RoleRoute allowedPermissions={['requests.create']}>
                    <CreateRequestPage />
                  </RoleRoute>
                }
              />
              <Route
                path="/requests/:id"
                element={
                  <RoleRoute allowedPermissions={['requests.read', 'department.requests.read']}>
                    <RequestDetailsPage />
                  </RoleRoute>
                }
              />
              <Route
                path="/requests/:id/contractor"
                element={
                  <RoleRoute allowedPermissions={[...REQUESTS_ROUTE_PERMISSIONS]}>
                    <ContractorRequestDetailsPage />
                  </RoleRoute>
                }
              />
              <Route path="/offers/:id/workspace" element={<OfferWorkspacePage />} />
              <Route
                path="/admin"
                element={
                  <RoleRoute allowedPermissions={['users.read']}>
                    <AdminPage />
                  </RoleRoute>
                }
              />
              <Route
                path="/contractors"
                element={
                  <RoleRoute allowedPermissions={['contractors.read']}>
                    <ContractorsPage />
                  </RoleRoute>
                }
              />
              <Route
                path="/feedback"
                element={
                  <RoleRoute allowedPermissions={['feedback.read']}>
                    <FeedbackPage />
                  </RoleRoute>
                }
              />
              <Route
                path="/pm-dashboard"
                element={
                  <RoleRoute allowedPermissions={['dashboard.process.read', 'department.dashboard.read']}>
                    <ProjectManagerDashboardPage />
                  </RoleRoute>
                }
              />
              <Route
                path="/pm-dashboard/savings"
                element={
                  <RoleRoute allowedPermissions={['dashboard.savings.read', 'department.dashboard.read']}>
                    <ProjectManagerSavingsPage />
                  </RoleRoute>
                }
              />
              <Route
                path="/pm-dashboard/plan"
                element={
                  <RoleRoute allowedPermissions={['dashboard.plans.read', 'department.plans.read', 'department.plans.manage']}>
                    <ProjectManagerPlanPage />
                  </RoleRoute>
                }
              />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to={hasSession ? defaultPath : '/login'} replace />} />
        </Routes>

        {backgroundLocation ? (
          <Routes>
            <Route element={<ProtectedRoute />}>
              <Route path="/requests/create" element={<CreateRequestPage />} />
            </Route>
          </Routes>
        ) : null}
      </Suspense>
    </>
  );
};
