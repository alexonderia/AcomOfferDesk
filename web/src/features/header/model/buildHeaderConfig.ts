import type { HeaderConfig, HeaderMobileNavItem } from './types';
import { ROLE } from '@shared/constants/roles';
import { isContractorRequestDetailsPath, isRequestDetailsPath } from '@shared/lib/routing/parseRequestRoutes';

type BuildHeaderConfigArgs = {
  roleId: number | null;
  pathname: string;
  canCreateRequest: boolean;
  canRegisterUser: boolean;
  canLoadOpenRequests: boolean;
  canLoadOfferedRequests: boolean;
  canOpenUsersPage: boolean;
  canOpenContractorsPage: boolean;
  canManageNormativeFiles: boolean;
  canViewFeedback: boolean;
  canViewDashboardProcess: boolean;
  canViewDashboardSavings: boolean;
  canViewDashboardPlans: boolean;
  breadcrumbs?: { key: string; label: string; to?: string }[];
  contractorTab: 'my' | 'open';
  adminUsersTab: 'contractors' | 'economists' | 'admins' | 'security_officers';
  onNavigateToDashboard: () => void;
  onNavigateToSavings: () => void;
  onNavigateToPlan: () => void;
  onNavigateToRequests: () => void;
  onNavigateToRequestCreate: () => void;
  onNavigateToAdmin: () => void;
  onNavigateToContractors: () => void;
  onNavigateToNormativeFiles: () => void;
  onNavigateToAdminCreate: () => void;
  onNavigateBackToRequests: () => void;
  onSetContractorTab: (_value: 'my' | 'open') => void;
  onSetAdminUsersTab: (_value: 'contractors' | 'economists' | 'admins' | 'security_officers') => void;
};

type MoreMenuOptions = {
  showProfile?: boolean;
  showContractors?: boolean;
  showNormative?: boolean;
  showRoleGuide?: boolean;
  showFeedback?: boolean;
  showLogout?: boolean;
};

const buildMoreNavItem = ({
  showProfile = true,
  showContractors = false,
  showNormative = false,
  showRoleGuide = true,
  showFeedback = true,
  showLogout = true,
}: MoreMenuOptions): HeaderMobileNavItem => {
  const children: HeaderMobileNavItem[] = [];

  if (showProfile) {
    children.push({ key: 'profile', label: 'Профиль' });
  }
  if (showContractors) {
    children.push({ key: 'contractors', label: 'Контрагенты', to: '/contractors' });
  }
  if (showNormative) {
    children.push({ key: 'normative', label: 'Нормативные документы', to: '/normative-files' });
  }
  if (showRoleGuide) {
    children.push({ key: 'guide', label: 'Памятка' });
  }
  if (showFeedback) {
    children.push({ key: 'feedback', label: 'Обратная связь' });
  }
  if (showLogout) {
    children.push({ key: 'logout', label: 'Выйти' });
  }

  return {
    key: 'more',
    label: 'Прочее',
    children,
  };
};

const buildSuperadminMobileNavItems = (
  showNormative: boolean,
  canOpenUsersPage: boolean,
  canViewFeedback: boolean,
  canViewDashboardProcess: boolean,
  canViewDashboardSavings: boolean,
  canViewDashboardPlans: boolean
): HeaderMobileNavItem[] => {
  const items: HeaderMobileNavItem[] = [];
  const dashboardChildren: HeaderMobileNavItem[] = [];
  if (canViewDashboardProcess) {
    dashboardChildren.push({ key: 'dashboard-process', label: 'Процесс работы', to: '/pm-dashboard' });
  }
  if (canViewDashboardSavings) {
    dashboardChildren.push({ key: 'dashboard-savings', label: 'Экономия', to: '/pm-dashboard/savings' });
  }
  if (canViewDashboardPlans) {
    dashboardChildren.push({ key: 'dashboard-plan', label: 'План', to: '/pm-dashboard/plan' });
  }
  if (dashboardChildren.length > 0) {
    items.push({
      key: 'dashboard',
      label: 'Дашборд',
      to: dashboardChildren[0].to,
      children: dashboardChildren,
    });
  }
  if (canOpenUsersPage) {
    items.push({ key: 'users', label: 'Пользователи', to: '/admin' });
  }
  items.push({ key: 'requests', label: 'Заявки', to: '/requests' });
  items.push(
    buildMoreNavItem({
      showProfile: false,
      showNormative,
      showRoleGuide: true,
      showFeedback: canViewFeedback,
      showLogout: true,
    })
  );
  return items;
};

const buildProjectManagerMobileNavItems = (
  showNormative: boolean,
  canOpenUsersPage: boolean,
  canOpenContractorsPage: boolean,
  canViewDashboardProcess: boolean,
  canViewDashboardSavings: boolean,
  canViewDashboardPlans: boolean
): HeaderMobileNavItem[] => {
  const dashboardChildren: HeaderMobileNavItem[] = [];
  if (canViewDashboardProcess) {
    dashboardChildren.push({ key: 'dashboard-process', label: 'Процесс работы', to: '/pm-dashboard' });
  }
  if (canViewDashboardSavings) {
    dashboardChildren.push({ key: 'dashboard-savings', label: 'Экономия', to: '/pm-dashboard/savings' });
  }
  if (canViewDashboardPlans) {
    dashboardChildren.push({ key: 'dashboard-plan', label: 'План', to: '/pm-dashboard/plan' });
  }
  const dashboardTarget = dashboardChildren[0]?.to ?? '/requests';
  const items: HeaderMobileNavItem[] = [
    {
      key: 'dashboard',
      label: 'Дашборд',
      to: dashboardTarget,
      children: dashboardChildren,
    },
    { key: 'requests', label: 'Заявки', to: '/requests' }
  ];

  if (canOpenUsersPage) {
    items.push({ key: 'employees', label: 'Сотрудники', to: '/admin' });
  }

  items.push(
    buildMoreNavItem({
      showProfile: true,
      showContractors: canOpenContractorsPage,
      showNormative,
      showRoleGuide: true,
      showFeedback: true,
      showLogout: true,
    })
  );

  return items;
};

const buildContractorMobileNavItems = (): HeaderMobileNavItem[] => [
  {
    key: 'requests',
    label: 'Заявки',
    children: [
      { key: 'my', label: 'Мои заявки', tabValue: 'my' },
      { key: 'open', label: 'Открытые', tabValue: 'open' },
    ],
  },
  buildMoreNavItem({
    showProfile: true,
    showNormative: false,
    showRoleGuide: true,
    showFeedback: true,
    showLogout: true,
  }),
];

const buildLeadMobileNavItems = (
  canViewDashboardPlans: boolean,
  canOpenUsersPage: boolean,
  canOpenContractorsPage: boolean
): HeaderMobileNavItem[] => {
  const items: HeaderMobileNavItem[] = [
    {
      key: 'dashboard',
      label: 'Дашборд',
      to: canViewDashboardPlans ? '/pm-dashboard/plan' : '/requests',
      children: canViewDashboardPlans ? [{ key: 'dashboard-plan', label: 'План', to: '/pm-dashboard/plan' }] : [],
    },
    { key: 'requests', label: 'Заявки', to: '/requests' },
  ];

  if (canOpenUsersPage) {
    items.push({ key: 'employees', label: 'Сотрудники', to: '/admin' });
  }

  items.push(
    buildMoreNavItem({
      showProfile: true,
      showContractors: canOpenContractorsPage,
      showNormative: false,
      showRoleGuide: true,
      showFeedback: true,
      showLogout: true,
    })
  );

  return items;
};

const buildEconomistMobileNavItems = (
  canViewDashboardPlans: boolean,
  canViewDashboardProcess: boolean,
  canViewDashboardSavings: boolean,
  canOpenUsersPage: boolean,
  canOpenContractorsPage: boolean
): HeaderMobileNavItem[] => {
  const items: HeaderMobileNavItem[] = [];
  const dashboardChildren: HeaderMobileNavItem[] = [];
  if (canViewDashboardProcess) {
    dashboardChildren.push({ key: 'dashboard-process', label: 'Процесс работы', to: '/pm-dashboard' });
  }
  if (canViewDashboardSavings) {
    dashboardChildren.push({ key: 'dashboard-savings', label: 'Экономия', to: '/pm-dashboard/savings' });
  }
  if (canViewDashboardPlans) {
    dashboardChildren.push({ key: 'dashboard-plan', label: 'План', to: '/pm-dashboard/plan' });
  }
  if (dashboardChildren.length > 0) {
    items.push({
      key: 'dashboard',
      label: '\u0414\u0430\u0448\u0431\u043e\u0440\u0434',
      to: dashboardChildren[0].to,
      children: dashboardChildren,
    });
  }

  items.push({ key: 'requests', label: '\u0417\u0430\u044f\u0432\u043a\u0438', to: '/requests' });

  if (canOpenUsersPage) {
    items.push({ key: 'employees', label: 'Сотрудники', to: '/admin' });
  }

  items.push(
    buildMoreNavItem({
      showProfile: true,
      showContractors: canOpenContractorsPage,
      showNormative: false,
      showRoleGuide: true,
      showFeedback: true,
      showLogout: true,
    })
  );

  return items;
};

const buildOperatorMobileNavItems = (): HeaderMobileNavItem[] => [
  { key: 'requests', label: '\u0417\u0430\u044f\u0432\u043a\u0438', to: '/requests' },
  buildMoreNavItem({
    showProfile: true,
    showNormative: false,
    showRoleGuide: true,
    showFeedback: true,
    showLogout: true,
  }),
];

const buildAdminMobileNavItems = (canOpenUsersPage: boolean): HeaderMobileNavItem[] => {
  const items: HeaderMobileNavItem[] = [];

  if (canOpenUsersPage) {
    items.push({ key: 'users', label: 'Пользователи', to: '/admin' });
  }

  items.push(
    buildMoreNavItem({
      showProfile: true,
      showNormative: false,
      showRoleGuide: true,
      showFeedback: true,
      showLogout: true,
    })
  );

  return items;
};

const buildSecurityOfficerMobileNavItems = (canOpenContractorsPage: boolean): HeaderMobileNavItem[] => {
  const items: HeaderMobileNavItem[] = [];

  if (canOpenContractorsPage) {
    items.push({ key: 'contractors', label: 'Контрагенты', to: '/contractors' });
  }

  items.push(
    buildMoreNavItem({
      showProfile: true,
      showContractors: false,
      showNormative: false,
      showRoleGuide: true,
      showFeedback: true,
      showLogout: true,
    })
  );

  return items;
};

const buildAdminUsersMobileNavItems = (): HeaderMobileNavItem[] => [
  {
    key: 'users',
    label: 'Пользователи',
    to: '/admin',
    children: [
      { key: 'contractors', label: 'Контрагенты', tabValue: 'contractors' },
      { key: 'economists', label: 'Экономисты', tabValue: 'economists' },
      { key: 'admins', label: 'Админы', tabValue: 'admins' },
      { key: 'security_officers', label: 'Служба безопасности', tabValue: 'security_officers' },
    ],
  },
  buildMoreNavItem({
    showProfile: true,
    showNormative: false,
    showRoleGuide: true,
    showFeedback: true,
    showLogout: true,
  }),
];

const resolveDefaultMobileNavItems = ({
  isSuperadmin,
  isProjectManager,
  isLeadEconomist,
  isContractor,
  isSecurityOfficer,
  isLeadLike,
  isEconomist,
  isOperator,
  isAdmin,
  canOpenUsersPage,
  canOpenContractorsPage,
  canManageNormativeFiles,
  canViewFeedback,
  canViewDashboardProcess,
  canViewDashboardSavings,
  canViewDashboardPlans,
}: {
  isSuperadmin: boolean;
  isProjectManager: boolean;
  isLeadEconomist: boolean;
  isContractor: boolean;
  isSecurityOfficer: boolean;
  isLeadLike: boolean;
  isEconomist: boolean;
  isOperator: boolean;
  isAdmin: boolean;
  canOpenUsersPage: boolean;
  canOpenContractorsPage: boolean;
  canManageNormativeFiles: boolean;
  canViewFeedback: boolean;
  canViewDashboardProcess: boolean;
  canViewDashboardSavings: boolean;
  canViewDashboardPlans: boolean;
}): HeaderMobileNavItem[] => {
  if (isSuperadmin) {
    return buildSuperadminMobileNavItems(
      canManageNormativeFiles,
      canOpenUsersPage,
      canViewFeedback,
      canViewDashboardProcess,
      canViewDashboardSavings,
      canViewDashboardPlans
    );
  }

  if (isProjectManager || isLeadEconomist) {
    return buildProjectManagerMobileNavItems(
      canManageNormativeFiles,
      canOpenUsersPage,
      canOpenContractorsPage,
      canViewDashboardProcess,
      canViewDashboardSavings,
      canViewDashboardPlans
    );
  }

  if (isContractor) {
    return buildContractorMobileNavItems();
  }

  if (isSecurityOfficer) {
    return buildSecurityOfficerMobileNavItems(canOpenContractorsPage);
  }

  if (isLeadLike && !isProjectManager && !isLeadEconomist) {
    if (isEconomist) {
      return buildEconomistMobileNavItems(
        canViewDashboardPlans,
        canViewDashboardProcess,
        canViewDashboardSavings,
        canOpenUsersPage,
        canOpenContractorsPage
      );
    }
    return buildLeadMobileNavItems(canViewDashboardPlans, canOpenUsersPage, canOpenContractorsPage);
  }

  if (isOperator) {
    return buildOperatorMobileNavItems();
  }

  return buildAdminMobileNavItems(isAdmin && canOpenUsersPage);
};

export const buildHeaderConfig = ({
  roleId,
  pathname,
  canCreateRequest: _canCreateRequest,
  canRegisterUser: _canRegisterUser,
  canLoadOpenRequests,
  canLoadOfferedRequests,
  canOpenUsersPage,
  canOpenContractorsPage,
  canManageNormativeFiles,
  canViewFeedback,
  canViewDashboardProcess,
  canViewDashboardSavings,
  canViewDashboardPlans,
  breadcrumbs = [],
  contractorTab,
  adminUsersTab,
  onNavigateToDashboard,
  onNavigateToSavings,
  onNavigateToPlan,
  onNavigateToRequests,
  onNavigateToRequestCreate: _onNavigateToRequestCreate,
  onNavigateToAdmin,
  onNavigateToContractors,
  onNavigateToNormativeFiles,
  onNavigateToAdminCreate: _onNavigateToAdminCreate,
  onNavigateBackToRequests,
  onSetContractorTab,
  onSetAdminUsersTab
}: BuildHeaderConfigArgs): HeaderConfig => {
  const isSuperadmin = roleId === ROLE.SUPERADMIN;
  const isAdmin = roleId === ROLE.ADMIN;
  const isContractor = roleId === ROLE.CONTRACTOR;
  const isSecurityOfficer = roleId === ROLE.SECURITY_OFFICER;
  const isLeadEconomist = roleId === ROLE.LEAD_ECONOMIST;
  const isProjectManager = roleId === ROLE.PROJECT_MANAGER;
  const isEconomist = roleId === ROLE.ECONOMIST;
  const isOperator = roleId === ROLE.OPERATOR;
  const isLeadLike = isLeadEconomist || isProjectManager || isEconomist;

  const isNormativeFilesPage = pathname === '/normative-files';
  const normativeNavProps = {
    showNormativeFiles: canManageNormativeFiles,
    normativeFilesActive: isNormativeFilesPage,
    onNavigateToNormativeFiles,
  };

  const isRequestsListPage = pathname === '/requests';
  const isRequestDetailsPage = isRequestDetailsPath(pathname);
  const isContractorRequestDetailsPage = isContractorRequestDetailsPath(pathname);
  const isOfferWorkspacePage = /^\/offers\/\d+\/workspace$/.test(pathname);
  const isResponsibilityDashboard =
    (isProjectManager || isLeadEconomist || isEconomist) && canViewDashboardProcess && pathname === '/pm-dashboard';
  const isResponsibilitySavings =
    (isProjectManager || isLeadEconomist || isEconomist) && canViewDashboardSavings && pathname === '/pm-dashboard/savings';
  const isResponsibilityPlan = isLeadLike && canViewDashboardPlans && pathname === '/pm-dashboard/plan';
  const isResponsibilityRequestsPage =
    (isProjectManager || isLeadEconomist) && (pathname.startsWith('/requests') || isOfferWorkspacePage);
  const isResponsibilityEmployeesPage = (isProjectManager || isLeadEconomist) && pathname.startsWith('/admin');
  const isResponsibilityContractorsPage = (isProjectManager || isLeadEconomist) && pathname.startsWith('/contractors');
  const isSuperadminDashboard = isSuperadmin && canViewDashboardProcess && pathname === '/pm-dashboard';
  const isSuperadminSavings = isSuperadmin && canViewDashboardSavings && pathname === '/pm-dashboard/savings';
  const isSuperadminPlan = isSuperadmin && canViewDashboardPlans && pathname === '/pm-dashboard/plan';
  const isSuperadminRequestsPage = isSuperadmin && (pathname.startsWith('/requests') || isOfferWorkspacePage);
  const isSuperadminUsersPage = isSuperadmin && pathname.startsWith('/admin');
  const isAdminUsersPage = isAdmin && pathname.startsWith('/admin');
  const isSecurityOfficerContractorsPage = isSecurityOfficer && pathname.startsWith('/contractors');

  const isContractorRequestsArea = isContractor
    && (isRequestsListPage || isContractorRequestDetailsPage || isOfferWorkspacePage);
  const canUseContractorTabs = isContractorRequestsArea && canLoadOpenRequests && canLoadOfferedRequests;
  const isLeadRequestsTab = isLeadLike && (pathname.startsWith('/requests') || isOfferWorkspacePage);
  const isLeadEconomistsTab = isLeadLike && pathname.startsWith('/admin');
  const isLeadPlanTab = isLeadLike && pathname === '/pm-dashboard/plan';
  const isLeadDashboardTab =
    isEconomist
    && ((canViewDashboardProcess && pathname === '/pm-dashboard')
      || (canViewDashboardSavings && pathname === '/pm-dashboard/savings'));
  const hasEconomistDashboardNav =
    canViewDashboardProcess || canViewDashboardSavings || canViewDashboardPlans;
  const canUseLeadTabs = isLeadLike && !isProjectManager && !isLeadEconomist
    && (isLeadRequestsTab || isLeadEconomistsTab || isLeadPlanTab || isLeadDashboardTab)
    && hasEconomistDashboardNav
    && (canOpenUsersPage || isEconomist);
  const canUseEconomistTabs = isEconomist
    && (pathname.startsWith('/requests') || pathname.startsWith('/admin') || pathname.startsWith('/contractors') || isOfferWorkspacePage)
    && canOpenUsersPage;
  const canUseOperatorTabs = isOperator && pathname.startsWith('/requests');
  const canUseSecurityOfficerTabs = isSecurityOfficer && canOpenContractorsPage && isSecurityOfficerContractorsPage;
  const canUseProjectManagerTabs = (isProjectManager || isLeadEconomist)
    && (canViewDashboardProcess || canViewDashboardSavings || canViewDashboardPlans || canOpenContractorsPage)
    && (
      isResponsibilityDashboard
      || isResponsibilitySavings
      || isResponsibilityPlan
      || isResponsibilityRequestsPage
      || isResponsibilityEmployeesPage
      || isResponsibilityContractorsPage
      || isNormativeFilesPage
    )
    && (canOpenUsersPage || canOpenContractorsPage);
  const canUseSuperadminTabs = isSuperadmin
    && (canViewDashboardProcess || canViewDashboardSavings || canViewDashboardPlans || canOpenUsersPage)
    && (isSuperadminDashboard || isSuperadminSavings || isSuperadminPlan || isSuperadminRequestsPage || isSuperadminUsersPage || isNormativeFilesPage);

  const defaultMobileNavItems = resolveDefaultMobileNavItems({
    isSuperadmin,
    isProjectManager,
    isLeadEconomist,
    isContractor,
    isSecurityOfficer,
    isLeadLike,
    isEconomist,
    isOperator,
    isAdmin,
    canOpenUsersPage,
    canOpenContractorsPage,
    canManageNormativeFiles,
    canViewFeedback,
    canViewDashboardProcess,
    canViewDashboardSavings,
    canViewDashboardPlans,
  });

  if (isSuperadmin) {
    const tabs = canUseSuperadminTabs
      ? [
        ...(canViewDashboardProcess ? [{ key: 'dashboard', value: 'dashboard', label: '\u0414\u0430\u0448\u0431\u043e\u0440\u0434' as const }] : []),
        ...(canViewDashboardSavings ? [{ key: 'savings', value: 'savings', label: '\u042d\u043a\u043e\u043d\u043e\u043c\u0438\u044f' as const }] : []),
        ...(canViewDashboardPlans ? [{ key: 'plan', value: 'plan', label: '\u041f\u043b\u0430\u043d' as const }] : []),
        { key: 'requests', value: 'requests', label: '\u0417\u0430\u044f\u0432\u043a\u0438' as const },
        ...(canOpenUsersPage ? [{ key: 'users', value: 'users', label: '\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0438' as const }] : []),
      ]
      : [];
    return {
      mode: 'sidebar',
      tabs,
      activeTab: isSuperadminDashboard
        ? 'dashboard'
        : isSuperadminSavings
          ? 'savings'
          : isSuperadminPlan
            ? 'plan'
            : isSuperadminUsersPage
              ? 'users'
              : isNormativeFilesPage
                ? 'normative'
                : 'requests',
      onTabChange: canUseSuperadminTabs
        ? (value) => {
          if (value === 'dashboard' && canViewDashboardProcess) {
            onNavigateToDashboard();
            return;
          }
          if (value === 'savings' && canViewDashboardSavings) {
            onNavigateToSavings();
            return;
          }
          if (value === 'plan' && canViewDashboardPlans) {
            onNavigateToPlan();
            return;
          }
          if (value === 'users' && canOpenUsersPage) {
            onNavigateToAdmin();
            return;
          }
          onNavigateToRequests();
        }
        : undefined,
      actions: [],
      breadcrumbs,
      mobileNavItems: buildSuperadminMobileNavItems(
        canManageNormativeFiles,
        canOpenUsersPage,
        canViewFeedback,
        canViewDashboardProcess,
        canViewDashboardSavings,
        canViewDashboardPlans
      ),
      showFeedback: true,
      showRoleGuide: true,
      showProfile: false,
      showLogout: true,
      ...normativeNavProps,
    };
  }

  if (canUseProjectManagerTabs) {
    return {
      mode: 'sidebar',
      breadcrumbs,
      mobileNavItems: buildProjectManagerMobileNavItems(
        canManageNormativeFiles,
        canOpenUsersPage,
        canOpenContractorsPage,
        canViewDashboardProcess,
        canViewDashboardSavings,
        canViewDashboardPlans
      ),
      tabs: [
        ...(canViewDashboardProcess ? [{ key: 'dashboard', value: 'dashboard', label: 'Дашборд' as const }] : []),
        ...(canViewDashboardSavings ? [{ key: 'savings', value: 'savings', label: 'Экономия' as const }] : []),
        ...(canViewDashboardPlans ? [{ key: 'plan', value: 'plan', label: 'План' as const }] : []),
        { key: 'requests', value: 'requests', label: 'Заявки' },
        ...(canOpenUsersPage ? [{ key: 'employees', value: 'employees', label: 'Сотрудники' as const }] : []),
        ...(canOpenContractorsPage ? [{ key: 'contractors', value: 'contractors', label: 'Контрагенты' as const }] : []),
      ],
      activeTab: isResponsibilityDashboard
        ? 'dashboard'
        : isResponsibilitySavings
          ? 'savings'
          : isResponsibilityPlan
            ? 'plan'
          : isResponsibilityEmployeesPage
            ? 'employees'
            : isResponsibilityContractorsPage
              ? 'contractors'
            : isNormativeFilesPage
              ? 'normative'
            : 'requests',
      onTabChange: (value) => {
        if (value === 'dashboard' && canViewDashboardProcess) {
          onNavigateToDashboard();
          return;
        }
        if (value === 'savings' && canViewDashboardSavings) {
          onNavigateToSavings();
          return;
        }
        if (value === 'plan' && canViewDashboardPlans) {
          onNavigateToPlan();
          return;
        }
        if (value === 'employees' && canOpenUsersPage) {
          onNavigateToAdmin();
          return;
        }
        if (value === 'contractors' && canOpenContractorsPage) {
          onNavigateToContractors();
          return;
        }
        onNavigateToRequests();
      },
      actions: [],
      showFeedback: true,
      showRoleGuide: true,
      showProfile: true,
      showLogout: true,
      ...normativeNavProps,
    };
  }

  if (isRequestDetailsPage) {
    return {
      mode: 'sidebar',
      breadcrumbs,
      tabs: [],
      actions: [],
      mobileNavItems: defaultMobileNavItems,
      backAction: {
        label: 'К списку заявок',
        onClick: onNavigateBackToRequests
      },
      showFeedback: true,
      showRoleGuide: true,
      showProfile: true,
      showLogout: true,
      ...normativeNavProps,
    };
  }

  if (canUseContractorTabs) {
    return {
      mode: 'sidebar',
      breadcrumbs,
      mobileNavItems: buildContractorMobileNavItems(),
      tabs: [
        { key: 'my', value: 'my', label: 'Мои заявки' },
        { key: 'open', value: 'open', label: 'Актуальные заявки' }
      ],
      activeTab: contractorTab,
      onTabChange: (value) => onSetContractorTab(value as 'my' | 'open'),
      actions: [],
      showFeedback: true,
      showRoleGuide: true,
      showProfile: true,
      showLogout: true,
      ...normativeNavProps,
    };
  }

  if (canUseLeadTabs) {
    return {
      mode: 'sidebar',
      breadcrumbs,
      mobileNavItems: buildEconomistMobileNavItems(
        canViewDashboardPlans,
        canViewDashboardProcess,
        canViewDashboardSavings,
        canOpenUsersPage,
        canOpenContractorsPage
      ),
      tabs: [
        ...(canViewDashboardProcess ? [{ key: 'dashboard', value: 'dashboard', label: 'Дашборд' as const }] : []),
        ...(canViewDashboardSavings ? [{ key: 'savings', value: 'savings', label: 'Экономия' as const }] : []),
        ...(canViewDashboardPlans ? [{ key: 'plan', value: 'plan', label: 'План' as const }] : []),
        { key: 'requests', value: 'requests', label: 'Заявки' },
        ...(canOpenUsersPage ? [{ key: 'economists', value: 'economists', label: 'Сотрудники' }] : []),
        ...(canOpenContractorsPage ? [{ key: 'contractors', value: 'contractors', label: 'Контрагенты' }] : []),
      ],
      activeTab: isResponsibilityDashboard
        ? 'dashboard'
        : isResponsibilitySavings
          ? 'savings'
          : isResponsibilityPlan
            ? 'plan'
            : pathname === '/admin'
              ? 'economists'
              : pathname.startsWith('/contractors')
                ? 'contractors'
              : 'requests',
      onTabChange: (value) => {
        if (value === 'dashboard' && canViewDashboardProcess) {
          onNavigateToDashboard();
          return;
        }
        if (value === 'savings' && canViewDashboardSavings) {
          onNavigateToSavings();
          return;
        }
        if (value === 'plan' && canViewDashboardPlans) {
          onNavigateToPlan();
          return;
        }
        if (value === 'economists' && canOpenUsersPage) {
          onNavigateToAdmin();
          return;
        }
        if (value === 'contractors' && canOpenContractorsPage) {
          onNavigateToContractors();
          return;
        }
        onNavigateToRequests();
      },
      actions: [],
      showFeedback: true,
      showRoleGuide: true,
      showProfile: true,
      showLogout: true,
      ...normativeNavProps,
    };
  }

  if (canUseEconomistTabs) {
    return {
      mode: 'sidebar',
      breadcrumbs,
      mobileNavItems: buildEconomistMobileNavItems(
        canViewDashboardPlans,
        canViewDashboardProcess,
        canViewDashboardSavings,
        canOpenUsersPage,
        canOpenContractorsPage
      ),
      tabs: [
        { key: 'requests', value: 'requests', label: '\u0417\u0430\u044f\u0432\u043a\u0438' },
        ...(canOpenUsersPage ? [{ key: 'economists', value: 'economists', label: 'Сотрудники' }] : []),
        ...(canOpenContractorsPage ? [{ key: 'contractors', value: 'contractors', label: 'Контрагенты' }] : []),
      ],
      activeTab: pathname.startsWith('/admin')
        ? 'economists'
        : pathname.startsWith('/contractors')
          ? 'contractors'
          : 'requests',
      onTabChange: (value) => {
        if (value === 'economists' && canOpenUsersPage) {
          onNavigateToAdmin();
          return;
        }
        if (value === 'contractors' && canOpenContractorsPage) {
          onNavigateToContractors();
          return;
        }
        onNavigateToRequests();
      },
      actions: [],
      showFeedback: true,
      showRoleGuide: true,
      showProfile: true,
      showLogout: true,
      ...normativeNavProps,
    };
  }

  if (canUseOperatorTabs) {
    return {
      mode: 'sidebar',
      breadcrumbs,
      mobileNavItems: buildOperatorMobileNavItems(),
      tabs: [{ key: 'requests', value: 'requests', label: '\u0417\u0430\u044f\u0432\u043a\u0438' }],
      activeTab: 'requests',
      onTabChange: () => {
        onNavigateToRequests();
      },
      actions: [],
      showFeedback: true,
      showRoleGuide: true,
      showProfile: true,
      showLogout: true,
      ...normativeNavProps,
    };
  }

  if (canUseSecurityOfficerTabs) {
    return {
      mode: 'sidebar',
      breadcrumbs,
      mobileNavItems: buildSecurityOfficerMobileNavItems(canOpenContractorsPage),
      tabs: [{ key: 'contractors', value: 'contractors', label: 'Контрагенты' }],
      activeTab: 'contractors',
      onTabChange: () => {
        onNavigateToContractors();
      },
      actions: [],
      showFeedback: true,
      showRoleGuide: true,
      showProfile: true,
      showLogout: true,
      ...normativeNavProps,
    };
  }

  if (isAdminUsersPage) {
    return {
      mode: 'sidebar',
      breadcrumbs,
      mobileNavItems: buildAdminUsersMobileNavItems(),
      tabs: [
        { key: 'contractors', value: 'contractors', label: 'Контрагенты' },
        { key: 'economists', value: 'economists', label: 'Экономисты' },
        { key: 'admins', value: 'admins', label: 'Администраторы' },
        { key: 'security_officers', value: 'security_officers', label: 'Служба безопасности' }
      ],
      activeTab: adminUsersTab,
      onTabChange: (value) => onSetAdminUsersTab(value as 'contractors' | 'economists' | 'admins' | 'security_officers'),
      actions: [],
      showFeedback: true,
      showRoleGuide: true,
      showProfile: true,
      showLogout: true,
      ...normativeNavProps,
    };
  }

  return {
    mode: 'sidebar',
    breadcrumbs,
    tabs: [],
    mobileNavItems: defaultMobileNavItems,
    actions: [],
    showFeedback: true,
    showRoleGuide: true,
    showProfile: true,
    showLogout: true,
    ...normativeNavProps,
  };
};
