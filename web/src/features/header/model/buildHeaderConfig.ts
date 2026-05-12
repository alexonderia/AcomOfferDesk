import type { HeaderConfig, HeaderMobileNavItem } from './types';
import { ROLE } from '@shared/constants/roles';

type BuildHeaderConfigArgs = {
  roleId: number | null;
  pathname: string;
  canCreateRequest: boolean;
  canRegisterUser: boolean;
  canLoadOpenRequests: boolean;
  canLoadOfferedRequests: boolean;
  canOpenUsersPage: boolean;
  canCreateNormativeFile: boolean;
  canViewFeedback: boolean;
  canViewDashboardProcess: boolean;
  canViewDashboardSavings: boolean;
  canViewDashboardPlans: boolean;
  breadcrumbs?: { key: string; label: string; to?: string }[];
  contractorTab: 'my' | 'open';
  adminUsersTab: 'contractors' | 'economists' | 'admins';
  onNavigateToDashboard: () => void;
  onNavigateToSavings: () => void;
  onNavigateToPlan: () => void;
  onNavigateToRequests: () => void;
  onNavigateToRequestCreate: () => void;
  onNavigateToAdmin: () => void;
  onNavigateToAdminCreate: () => void;
  onNavigateBackToRequests: () => void;
  onSetContractorTab: (value: 'my' | 'open') => void;
  onSetAdminUsersTab: (value: 'contractors' | 'economists' | 'admins') => void;
};

type MoreMenuOptions = {
  showProfile?: boolean;
  showNormative?: boolean;
  showRoleGuide?: boolean;
  showFeedback?: boolean;
  showLogout?: boolean;
};

const buildMoreNavItem = ({
  showProfile = true,
  showNormative = false,
  showRoleGuide = true,
  showFeedback = true,
  showLogout = true,
}: MoreMenuOptions): HeaderMobileNavItem => {
  const children: HeaderMobileNavItem[] = [];

  if (showProfile) {
    children.push({ key: 'profile', label: 'Профиль' });
  }
  if (showNormative) {
    children.push({ key: 'normative', label: 'Нормативные документы' });
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
    items.push({ key: 'employees', label: 'Штат сотрудников', to: '/admin' });
  }

  items.push(
    buildMoreNavItem({
      showProfile: true,
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

const buildLeadMobileNavItems = (canViewDashboardPlans: boolean): HeaderMobileNavItem[] => [
  {
    key: 'dashboard',
    label: 'Дашборд',
    to: canViewDashboardPlans ? '/pm-dashboard/plan' : '/requests',
    children: canViewDashboardPlans ? [{ key: 'dashboard-plan', label: 'План', to: '/pm-dashboard/plan' }] : [],
  },
  { key: 'requests', label: 'Заявки', to: '/requests' },
  { key: 'economists', label: 'Экономисты', to: '/admin' },
  buildMoreNavItem({
    showProfile: true,
    showNormative: false,
    showRoleGuide: true,
    showFeedback: true,
    showLogout: true,
  }),
];

const buildEconomistMobileNavItems = (canViewDashboardPlans: boolean, canOpenUsersPage: boolean): HeaderMobileNavItem[] => {
  const items: HeaderMobileNavItem[] = [];

  if (canViewDashboardPlans) {
    items.push({
      key: 'dashboard',
      label: '\u0414\u0430\u0448\u0431\u043e\u0440\u0434',
      to: '/pm-dashboard/plan',
      children: [{ key: 'dashboard-plan', label: '\u041f\u043b\u0430\u043d', to: '/pm-dashboard/plan' }],
    });
  }

  items.push({ key: 'requests', label: '\u0417\u0430\u044f\u0432\u043a\u0438', to: '/requests' });

  if (canOpenUsersPage) {
    items.push({ key: 'economists', label: '\u042d\u043a\u043e\u043d\u043e\u043c\u0438\u0441\u0442\u044b', to: '/admin' });
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

const buildAdminUsersMobileNavItems = (): HeaderMobileNavItem[] => [
  {
    key: 'users',
    label: 'Пользователи',
    to: '/admin',
    children: [
      { key: 'contractors', label: 'Контрагенты', tabValue: 'contractors' },
      { key: 'economists', label: 'Экономисты', tabValue: 'economists' },
      { key: 'admins', label: 'Админы', tabValue: 'admins' },
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
  isLeadLike,
  isEconomist,
  isOperator,
  isAdmin,
  canOpenUsersPage,
  canCreateNormativeFile,
  canViewFeedback,
  canViewDashboardProcess,
  canViewDashboardSavings,
  canViewDashboardPlans,
}: {
  isSuperadmin: boolean;
  isProjectManager: boolean;
  isLeadEconomist: boolean;
  isContractor: boolean;
  isLeadLike: boolean;
  isEconomist: boolean;
  isOperator: boolean;
  isAdmin: boolean;
  canOpenUsersPage: boolean;
  canCreateNormativeFile: boolean;
  canViewFeedback: boolean;
  canViewDashboardProcess: boolean;
  canViewDashboardSavings: boolean;
  canViewDashboardPlans: boolean;
}): HeaderMobileNavItem[] => {
  if (isSuperadmin) {
    return buildSuperadminMobileNavItems(
      canCreateNormativeFile,
      canOpenUsersPage,
      canViewFeedback,
      canViewDashboardProcess,
      canViewDashboardSavings,
      canViewDashboardPlans
    );
  }

  if (isProjectManager || isLeadEconomist) {
    return buildProjectManagerMobileNavItems(
      canCreateNormativeFile,
      canOpenUsersPage,
      canViewDashboardProcess,
      canViewDashboardSavings,
      canViewDashboardPlans
    );
  }

  if (isContractor) {
    return buildContractorMobileNavItems();
  }

  if (isLeadLike && !isProjectManager && !isLeadEconomist) {
    if (isEconomist) {
      return buildEconomistMobileNavItems(canViewDashboardPlans, canOpenUsersPage);
    }
    return buildLeadMobileNavItems(canViewDashboardPlans);
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
  canCreateNormativeFile,
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
  onNavigateToAdminCreate: _onNavigateToAdminCreate,
  onNavigateBackToRequests,
  onSetContractorTab,
  onSetAdminUsersTab
}: BuildHeaderConfigArgs): HeaderConfig => {
  const isSuperadmin = roleId === ROLE.SUPERADMIN;
  const isAdmin = roleId === ROLE.ADMIN;
  const isContractor = roleId === ROLE.CONTRACTOR;
  const isLeadEconomist = roleId === ROLE.LEAD_ECONOMIST;
  const isProjectManager = roleId === ROLE.PROJECT_MANAGER;
  const isEconomist = roleId === ROLE.ECONOMIST;
  const isOperator = roleId === ROLE.OPERATOR;
  const isLeadLike = isLeadEconomist || isProjectManager || isEconomist;

  const isRequestsListPage = pathname === '/requests';
  const isRequestDetailsPage = /^\/requests\/\d+$/.test(pathname);
  const isContractorRequestDetailsPage = /^\/requests\/\d+\/contractor$/.test(pathname);
  const isOfferWorkspacePage = /^\/offers\/\d+\/workspace$/.test(pathname);
  const isResponsibilityDashboard = (isProjectManager || isLeadEconomist) && canViewDashboardProcess && pathname === '/pm-dashboard';
  const isResponsibilitySavings = (isProjectManager || isLeadEconomist) && canViewDashboardSavings && pathname === '/pm-dashboard/savings';
  const isResponsibilityPlan = isLeadLike && canViewDashboardPlans && pathname === '/pm-dashboard/plan';
  const isResponsibilityRequestsPage =
    (isProjectManager || isLeadEconomist) && (pathname.startsWith('/requests') || isOfferWorkspacePage);
  const isResponsibilityEmployeesPage = (isProjectManager || isLeadEconomist) && pathname.startsWith('/admin');
  const isSuperadminDashboard = isSuperadmin && canViewDashboardProcess && pathname === '/pm-dashboard';
  const isSuperadminSavings = isSuperadmin && canViewDashboardSavings && pathname === '/pm-dashboard/savings';
  const isSuperadminPlan = isSuperadmin && canViewDashboardPlans && pathname === '/pm-dashboard/plan';
  const isSuperadminRequestsPage = isSuperadmin && (pathname.startsWith('/requests') || isOfferWorkspacePage);
  const isSuperadminUsersPage = isSuperadmin && pathname.startsWith('/admin');
  const isAdminUsersPage = isAdmin && pathname.startsWith('/admin');

  const isContractorRequestsArea = isContractor
    && (isRequestsListPage || isContractorRequestDetailsPage || isOfferWorkspacePage);
  const canUseContractorTabs = isContractorRequestsArea && canLoadOpenRequests && canLoadOfferedRequests;
  const isLeadRequestsTab = isLeadLike && (pathname.startsWith('/requests') || isOfferWorkspacePage);
  const isLeadEconomistsTab = isLeadLike && pathname.startsWith('/admin');
  const isLeadPlanTab = isLeadLike && pathname === '/pm-dashboard/plan';
  const canUseLeadTabs = isLeadLike && !isProjectManager && !isLeadEconomist
    && (isLeadRequestsTab || isLeadEconomistsTab || isLeadPlanTab)
    && canViewDashboardPlans
    && (canOpenUsersPage || isEconomist);
  const canUseEconomistTabs = isEconomist
    && (pathname.startsWith('/requests') || pathname.startsWith('/admin') || isOfferWorkspacePage)
    && canOpenUsersPage;
  const canUseOperatorTabs = isOperator && pathname.startsWith('/requests');
  const canUseProjectManagerTabs = (isProjectManager || isLeadEconomist)
    && (canViewDashboardProcess || canViewDashboardSavings || canViewDashboardPlans)
    && (isResponsibilityDashboard || isResponsibilitySavings || isResponsibilityPlan || isResponsibilityRequestsPage || isResponsibilityEmployeesPage)
    && canOpenUsersPage;
  const canUseSuperadminTabs = isSuperadmin
    && (canViewDashboardProcess || canViewDashboardSavings || canViewDashboardPlans || canOpenUsersPage)
    && (isSuperadminDashboard || isSuperadminSavings || isSuperadminPlan || isSuperadminRequestsPage || isSuperadminUsersPage);

  const defaultMobileNavItems = resolveDefaultMobileNavItems({
    isSuperadmin,
    isProjectManager,
    isLeadEconomist,
    isContractor,
    isLeadLike,
    isEconomist,
    isOperator,
    isAdmin,
    canOpenUsersPage,
    canCreateNormativeFile,
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
        canCreateNormativeFile,
        canOpenUsersPage,
        canViewFeedback,
        canViewDashboardProcess,
        canViewDashboardSavings,
        canViewDashboardPlans
      ),
      showFeedback: true,
      showRoleGuide: true,
      showProfile: false,
      showLogout: true
    };
  }

  if (canUseProjectManagerTabs) {
    return {
      mode: 'sidebar',
      breadcrumbs,
      mobileNavItems: buildProjectManagerMobileNavItems(
        canCreateNormativeFile,
        canOpenUsersPage,
        canViewDashboardProcess,
        canViewDashboardSavings,
        canViewDashboardPlans
      ),
      tabs: [
        ...(canViewDashboardProcess ? [{ key: 'dashboard', value: 'dashboard', label: 'Дашборд' as const }] : []),
        ...(canViewDashboardSavings ? [{ key: 'savings', value: 'savings', label: 'Экономия' as const }] : []),
        ...(canViewDashboardPlans ? [{ key: 'plan', value: 'plan', label: 'План' as const }] : []),
        { key: 'requests', value: 'requests', label: 'Заявки' },
        { key: 'employees', value: 'employees', label: 'Сотрудники' }
      ],
      activeTab: isResponsibilityDashboard
        ? 'dashboard'
        : isResponsibilitySavings
          ? 'savings'
          : isResponsibilityPlan
            ? 'plan'
          : isResponsibilityEmployeesPage
            ? 'employees'
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
        if (value === 'employees') {
          onNavigateToAdmin();
          return;
        }
        onNavigateToRequests();
      },
      actions: [],
      showFeedback: true,
      showRoleGuide: true,
      showProfile: true,
      showLogout: true
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
      showLogout: true
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
      showLogout: true
    };
  }

  if (canUseLeadTabs) {
    return {
      mode: 'sidebar',
      breadcrumbs,
      mobileNavItems: buildLeadMobileNavItems(canViewDashboardPlans),
      tabs: [
        { key: 'dashboard', value: 'dashboard', label: 'Дашборд' },
        { key: 'plan', value: 'plan', label: 'План' },
        { key: 'requests', value: 'requests', label: 'Заявки' },
        { key: 'economists', value: 'economists', label: 'Экономисты' }
      ],
      activeTab: pathname === '/pm-dashboard/plan' ? 'plan' : pathname === '/admin' ? 'economists' : 'requests',
      onTabChange: (value) => {
        if ((value === 'dashboard' || value === 'plan') && canViewDashboardPlans) {
          onNavigateToPlan();
          return;
        }
        if (value === 'economists') {
          onNavigateToAdmin();
          return;
        }
        onNavigateToRequests();
      },
      actions: [],
      showFeedback: true,
      showRoleGuide: true,
      showProfile: true,
      showLogout: true
    };
  }

  if (canUseEconomistTabs) {
    return {
      mode: 'sidebar',
      breadcrumbs,
      mobileNavItems: buildEconomistMobileNavItems(canViewDashboardPlans, canOpenUsersPage),
      tabs: [
        { key: 'requests', value: 'requests', label: '\u0417\u0430\u044f\u0432\u043a\u0438' },
        ...(canOpenUsersPage ? [{ key: 'economists', value: 'economists', label: '\u042d\u043a\u043e\u043d\u043e\u043c\u0438\u0441\u0442\u044b' }] : []),
      ],
      activeTab: pathname.startsWith('/admin') ? 'economists' : 'requests',
      onTabChange: (value) => {
        if (value === 'economists' && canOpenUsersPage) {
          onNavigateToAdmin();
          return;
        }
        onNavigateToRequests();
      },
      actions: [],
      showFeedback: true,
      showRoleGuide: true,
      showProfile: true,
      showLogout: true
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
      showLogout: true
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
        { key: 'admins', value: 'admins', label: 'Администраторы' }
      ],
      activeTab: adminUsersTab,
      onTabChange: (value) => onSetAdminUsersTab(value as 'contractors' | 'economists' | 'admins'),
      actions: [],
      showFeedback: true,
      showRoleGuide: true,
      showProfile: true,
      showLogout: true
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
    showLogout: true
  };
};
