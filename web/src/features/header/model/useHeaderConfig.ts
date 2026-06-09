import { useMemo } from 'react';
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@app/providers/AuthProvider';
import { hasPermission } from '@shared/auth/permissions';
import { ROLE } from '@shared/constants/roles';
import { matchContractorRequestDetailsPath, matchRequestDetailsPath } from '@shared/lib/routing/parseRequestRoutes';
import { buildHeaderConfig } from './buildHeaderConfig';

export const useHeaderConfig = () => {
  const { session } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const contractorTabParam = searchParams.get('tab');
  const contractorTab: 'my' | 'open' = contractorTabParam === 'open' ? 'open' : 'my';

  const adminUsersTabParam = searchParams.get('users_tab');
  const adminUsersTab: 'contractors' | 'economists' | 'admins' | 'security_officers' =
    adminUsersTabParam === 'economists'
    || adminUsersTabParam === 'admins'
    || adminUsersTabParam === 'security_officers'
      ? adminUsersTabParam
      : 'contractors';

  const canCreateRequest = hasPermission(session, 'requests.create');
  const canLoadOpenRequests = hasPermission(session, 'requests.open.read');
  const canLoadOfferedRequests = hasPermission(session, 'requests.offered.read');
  const canOpenUsersPage = hasPermission(session, 'users.read');
  const canOpenContractorsPage = hasPermission(session, 'contractors.read');
  const canRegisterUser = hasPermission(session, 'users.create');
  const canManageNormativeFiles = hasPermission(session, 'normative_files.manage');
  const canViewFeedback = hasPermission(session, 'feedback.read');
  const canViewDashboardProcess = hasPermission(session, 'dashboard.process.read')
    || hasPermission(session, 'department.dashboard.read');
  const canViewDashboardSavings = hasPermission(session, 'dashboard.savings.read')
    || hasPermission(session, 'department.dashboard.read');
  const canViewDashboardPlans = hasPermission(session, 'dashboard.plans.read')
    || hasPermission(session, 'department.plans.read')
    || hasPermission(session, 'department.plans.manage');
  const isContractor = session?.roleId === ROLE.CONTRACTOR;
  const requestId = matchRequestDetailsPath(location.pathname);
  const contractorRequestId = matchContractorRequestDetailsPath(location.pathname);
  const offerMatch = location.pathname.match(/^\/offers\/(\d+)\/workspace$/);
  const offerRequestIdParam = searchParams.get('requestId');
  const isPmDashboard = location.pathname === '/pm-dashboard';
  const isPmSavings = location.pathname === '/pm-dashboard/savings';
  const isPmPlan = location.pathname === '/pm-dashboard/plan';
  const isRequestCreatePage = location.pathname === '/requests/create';

  const breadcrumbs = useMemo(() => {
    if (location.pathname === '/admin') {
      const isEmployeesPage =
        session?.roleId === ROLE.PROJECT_MANAGER
        || session?.roleId === ROLE.LEAD_ECONOMIST
        || session?.roleId === ROLE.ECONOMIST;
      return [{ key: 'users', label: isEmployeesPage ? 'Сотрудники' : 'Пользователи' }];
    }

    if (location.pathname === '/contractors') {
      return [{ key: 'contractors', label: 'Контрагенты' }];
    }

    if (location.pathname === '/requests') {
      return [{ key: 'requests', label: 'Заявки' }];
    }

    if (isRequestCreatePage) {
      return [
        { key: 'requests', label: 'Заявки', to: '/requests' },
        { key: 'request-create', label: 'Создание заявки' },
      ];
    }

    if (location.pathname === '/normative-files') {
      return [{ key: 'normative-files', label: 'Нормативные документы' }];
    }

    if (isPmDashboard) {
      return [{ key: 'pm-dashboard', label: 'Дашборд' }];
    }

    if (isPmSavings) {
      return [
        { key: 'pm-dashboard', label: 'Дашборд', to: '/pm-dashboard' },
        { key: 'pm-savings', label: 'Экономия' },
      ];
    }

    if (isPmPlan) {
      return [
        { key: 'pm-dashboard', label: 'Дашборд', to: '/pm-dashboard' },
        { key: 'pm-plan', label: 'План' },
      ];
    }

    if (requestId) {
      return [
        { key: 'requests', label: 'Заявки', to: '/requests' },
        { key: `request-${requestId}`, label: `Заявка №${requestId}` },
      ];
    }

    if (contractorRequestId) {
      return [
        { key: 'requests', label: 'Заявки', to: '/requests' },
        { key: `contractor-request-${contractorRequestId}`, label: `Заявка №${contractorRequestId}` },
      ];
    }

    if (offerMatch) {
      if (isContractor) {
        return [
          { key: 'requests-my', label: 'Мои заявки', to: '/requests?tab=my' },
          { key: `offer-${offerMatch[1]}`, label: `КП №${offerMatch[1]}` },
        ];
      }
      const requestCrumb = offerRequestIdParam
        ? { key: `request-${offerRequestIdParam}`, label: `Заявка №${offerRequestIdParam}`, to: `/requests/${offerRequestIdParam}` }
        : { key: 'request-details', label: 'Заявка', to: '/requests' };
      return [
        { key: 'requests', label: 'Заявки', to: '/requests' },
        requestCrumb,
        { key: `offer-${offerMatch[1]}`, label: `КП №${offerMatch[1]}` },
      ];
    }

    return [];
  }, [contractorRequestId, isContractor, isPmDashboard, isPmPlan, isPmSavings, isRequestCreatePage, location.pathname, offerMatch, offerRequestIdParam, requestId, session?.roleId]);

  return useMemo(
    () =>
      buildHeaderConfig({
        roleId: session?.roleId ?? null,
        pathname: location.pathname,
        canCreateRequest,
        canRegisterUser,
        canLoadOpenRequests,
        canLoadOfferedRequests,
        canOpenUsersPage,
        canOpenContractorsPage,
        canManageNormativeFiles,
        canViewFeedback,
        canViewDashboardProcess,
        canViewDashboardSavings,
        canViewDashboardPlans,
        breadcrumbs,
        contractorTab,
        adminUsersTab,
        onNavigateToDashboard: () => navigate('/pm-dashboard'),
        onNavigateToSavings: () => navigate('/pm-dashboard/savings'),
        onNavigateToPlan: () => navigate('/pm-dashboard/plan'),
        onNavigateToRequests: () => navigate('/requests'),
        onNavigateToRequestCreate: () => navigate('/requests/create', { state: { backgroundLocation: location } }),
        onNavigateToAdmin: () => navigate('/admin'),
        onNavigateToContractors: () => navigate('/contractors'),
        onNavigateToNormativeFiles: () => navigate('/normative-files'),
        onNavigateToAdminCreate: () => {
          const params = new URLSearchParams(searchParams);
          if (location.pathname.startsWith('/admin')) {
            params.set('users_tab', adminUsersTab);
          }
          params.set('create', '1');
          navigate(`/admin?${params.toString()}`);
        },
        onNavigateBackToRequests: () => navigate('/requests'),
        onSetContractorTab: (value) => {
          if (location.pathname !== '/requests') {
            navigate(`/requests?tab=${value}`);
            return;
          }
          setSearchParams((prev) => {
            const next = new URLSearchParams(prev);
            next.set('tab', value);
            return next;
          }, { replace: true });
        },
        onSetAdminUsersTab: (value) => {
          setSearchParams((prev) => {
            const next = new URLSearchParams(prev);
            next.set('users_tab', value);
            return next;
          }, { replace: true });
        }
      }),
    [
      adminUsersTab,
      canCreateRequest,
      canLoadOfferedRequests,
      canLoadOpenRequests,
      canOpenUsersPage,
      canOpenContractorsPage,
      canManageNormativeFiles,
      canViewFeedback,
      canViewDashboardProcess,
      canViewDashboardSavings,
      canViewDashboardPlans,
      canRegisterUser,
      contractorTab,
      breadcrumbs,
      location,
      navigate,
      searchParams,
      session?.roleId,
      setSearchParams
    ]
  );
};
