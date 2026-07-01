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
  canOpenHierarchyPage: boolean;
  canOpenContractorsPage: boolean;
  canManageNormativeFiles: boolean;
  canViewFeedback: boolean;
  canViewDashboardProcess: boolean;
  canViewDashboardSavings: boolean;
  canViewDashboardPlans: boolean;
  breadcrumbs?: { key: string; label: string; to?: string }[];
  contractorTab: 'my' | 'open';
  onNavigateToDashboard: () => void;
  onNavigateToSavings: () => void;
  onNavigateToPlan: () => void;
  onNavigateToRequests: () => void;
  onNavigateToRequestCreate: () => void;
  onNavigateToAdmin: () => void;
  onNavigateToHierarchy: () => void;
  onNavigateToContractors: () => void;
  onNavigateToNormativeFiles: () => void;
  onNavigateToAdminCreate: () => void;
  onNavigateBackToRequests: () => void;
  onSetContractorTab: (_value: 'my' | 'open') => void;
};

type MoreMenuOptions = {
  showProfile?: boolean;
  showContractors?: boolean;
  showNormative?: boolean;
  showRoleGuide?: boolean;
  showFeedback?: boolean;
  showLogout?: boolean;
};

const LABELS = {
  profile: '\u041f\u0440\u043e\u0444\u0438\u043b\u044c',
  contractors: '\u041a\u043e\u043d\u0442\u0440\u0430\u0433\u0435\u043d\u0442\u044b',
  normative: '\u041d\u043e\u0440\u043c\u0430\u0442\u0438\u0432\u043d\u044b\u0435 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u044b',
  guide: '\u041f\u0430\u043c\u044f\u0442\u043a\u0430',
  feedback: '\u041e\u0431\u0440\u0430\u0442\u043d\u0430\u044f \u0441\u0432\u044f\u0437\u044c',
  logout: '\u0412\u044b\u0439\u0442\u0438',
  more: '\u041f\u0440\u043e\u0447\u0435\u0435',
  dashboard: '\u0414\u0430\u0448\u0431\u043e\u0440\u0434',
  dashboardProcess: '\u041f\u0440\u043e\u0446\u0435\u0441\u0441 \u0440\u0430\u0431\u043e\u0442\u044b',
  savings: '\u042d\u043a\u043e\u043d\u043e\u043c\u0438\u044f',
  plan: '\u041f\u043b\u0430\u043d',
  requests: '\u0417\u0430\u044f\u0432\u043a\u0438',
  users: '\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0438',
  employees: '\u0421\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a\u0438',
  hierarchy: '\u0418\u0435\u0440\u0430\u0440\u0445\u0438\u044f',
  myRequests: '\u041c\u043e\u0438 \u0437\u0430\u044f\u0432\u043a\u0438',
  openRequests: '\u041e\u0442\u043a\u0440\u044b\u0442\u044b\u0435',
  activeRequests: '\u0410\u043a\u0442\u0443\u0430\u043b\u044c\u043d\u044b\u0435 \u0437\u0430\u044f\u0432\u043a\u0438',
} as const;

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
    children.push({ key: 'profile', label: LABELS.profile });
  }
  if (showContractors) {
    children.push({ key: 'contractors', label: LABELS.contractors, to: '/contractors' });
  }
  if (showNormative) {
    children.push({ key: 'normative', label: LABELS.normative, to: '/normative-files' });
  }
  if (showRoleGuide) {
    children.push({ key: 'guide', label: LABELS.guide });
  }
  if (showFeedback) {
    children.push({ key: 'feedback', label: LABELS.feedback });
  }
  if (showLogout) {
    children.push({ key: 'logout', label: LABELS.logout });
  }

  return {
    key: 'more',
    label: LABELS.more,
    children,
  };
};

const buildDashboardChildren = (
  canViewDashboardProcess: boolean,
  canViewDashboardSavings: boolean,
  canViewDashboardPlans: boolean
): HeaderMobileNavItem[] => {
  const dashboardChildren: HeaderMobileNavItem[] = [];

  if (canViewDashboardProcess) {
    dashboardChildren.push({ key: 'dashboard-process', label: LABELS.dashboardProcess, to: '/pm-dashboard' });
  }
  if (canViewDashboardSavings) {
    dashboardChildren.push({ key: 'dashboard-savings', label: LABELS.savings, to: '/pm-dashboard/savings' });
  }
  if (canViewDashboardPlans) {
    dashboardChildren.push({ key: 'dashboard-plan', label: LABELS.plan, to: '/pm-dashboard/plan' });
  }

  return dashboardChildren;
};

const buildSuperadminMobileNavItems = (
  showNormative: boolean,
  canOpenUsersPage: boolean,
  canOpenHierarchyPage: boolean,
  canViewFeedback: boolean,
  canViewDashboardProcess: boolean,
  canViewDashboardSavings: boolean,
  canViewDashboardPlans: boolean
): HeaderMobileNavItem[] => {
  const items: HeaderMobileNavItem[] = [];
  const dashboardChildren = buildDashboardChildren(
    canViewDashboardProcess,
    canViewDashboardSavings,
    canViewDashboardPlans
  );

  if (dashboardChildren.length > 0) {
    items.push({
      key: 'dashboard',
      label: LABELS.dashboard,
      to: dashboardChildren[0].to,
      children: dashboardChildren,
    });
  }
  if (canOpenUsersPage) {
    items.push({ key: 'users', label: LABELS.users, to: '/admin' });
  }
  if (canOpenHierarchyPage) {
    items.push({ key: 'hierarchy', label: LABELS.hierarchy, to: '/admin/hierarchy' });
  }
  items.push({ key: 'requests', label: LABELS.requests, to: '/requests' });
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
  canOpenHierarchyPage: boolean,
  canOpenContractorsPage: boolean,
  canViewDashboardProcess: boolean,
  canViewDashboardSavings: boolean,
  canViewDashboardPlans: boolean
): HeaderMobileNavItem[] => {
  const dashboardChildren = buildDashboardChildren(
    canViewDashboardProcess,
    canViewDashboardSavings,
    canViewDashboardPlans
  );
  const dashboardTarget = dashboardChildren[0]?.to ?? '/requests';
  const items: HeaderMobileNavItem[] = [
    {
      key: 'dashboard',
      label: LABELS.dashboard,
      to: dashboardTarget,
      children: dashboardChildren,
    },
    { key: 'requests', label: LABELS.requests, to: '/requests' },
  ];

  if (canOpenUsersPage) {
    items.push({ key: 'employees', label: LABELS.employees, to: '/admin' });
  }
  if (canOpenHierarchyPage) {
    items.push({ key: 'hierarchy', label: LABELS.hierarchy, to: '/admin/hierarchy' });
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
    label: LABELS.requests,
    children: [
      { key: 'my', label: LABELS.myRequests, tabValue: 'my' },
      { key: 'open', label: LABELS.openRequests, tabValue: 'open' },
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
      label: LABELS.dashboard,
      to: canViewDashboardPlans ? '/pm-dashboard/plan' : '/requests',
      children: canViewDashboardPlans ? [{ key: 'dashboard-plan', label: LABELS.plan, to: '/pm-dashboard/plan' }] : [],
    },
    { key: 'requests', label: LABELS.requests, to: '/requests' },
  ];

  if (canOpenUsersPage) {
    items.push({ key: 'employees', label: LABELS.employees, to: '/admin' });
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
  canOpenHierarchyPage: boolean,
  canOpenContractorsPage: boolean
): HeaderMobileNavItem[] => {
  const items: HeaderMobileNavItem[] = [];
  const dashboardChildren = buildDashboardChildren(
    canViewDashboardProcess,
    canViewDashboardSavings,
    canViewDashboardPlans
  );

  if (dashboardChildren.length > 0) {
    items.push({
      key: 'dashboard',
      label: LABELS.dashboard,
      to: dashboardChildren[0].to,
      children: dashboardChildren,
    });
  }

  items.push({ key: 'requests', label: LABELS.requests, to: '/requests' });

  if (canOpenUsersPage) {
    items.push({ key: 'employees', label: LABELS.employees, to: '/admin' });
  }
  if (canOpenHierarchyPage) {
    items.push({ key: 'hierarchy', label: LABELS.hierarchy, to: '/admin/hierarchy' });
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
  { key: 'requests', label: LABELS.requests, to: '/requests' },
  buildMoreNavItem({
    showProfile: true,
    showNormative: false,
    showRoleGuide: true,
    showFeedback: true,
    showLogout: true,
  }),
];

const buildAdminMobileNavItems = (canOpenUsersPage: boolean, canOpenHierarchyPage: boolean): HeaderMobileNavItem[] => {
  const items: HeaderMobileNavItem[] = [];

  if (canOpenUsersPage) {
    items.push({ key: 'users', label: LABELS.users, to: '/admin' });
  }
  if (canOpenHierarchyPage) {
    items.push({ key: 'hierarchy', label: LABELS.hierarchy, to: '/admin/hierarchy' });
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
    items.push({ key: 'contractors', label: LABELS.contractors, to: '/contractors' });
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
  canOpenHierarchyPage,
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
  canOpenHierarchyPage: boolean;
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
      canOpenHierarchyPage,
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
      canOpenHierarchyPage,
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
        canOpenHierarchyPage,
        canOpenContractorsPage
      );
    }

    return buildLeadMobileNavItems(canViewDashboardPlans, canOpenUsersPage, canOpenContractorsPage);
  }

  if (isOperator) {
    return buildOperatorMobileNavItems();
  }

  return buildAdminMobileNavItems(isAdmin && canOpenUsersPage, isAdmin && canOpenHierarchyPage);
};

export const buildHeaderConfig = ({
  roleId,
  pathname,
  canCreateRequest: _canCreateRequest,
  canRegisterUser: _canRegisterUser,
  canLoadOpenRequests,
  canLoadOfferedRequests,
  canOpenUsersPage,
  canOpenHierarchyPage,
  canOpenContractorsPage,
  canManageNormativeFiles,
  canViewFeedback,
  canViewDashboardProcess,
  canViewDashboardSavings,
  canViewDashboardPlans,
  breadcrumbs = [],
  contractorTab,
  onNavigateToDashboard,
  onNavigateToSavings,
  onNavigateToPlan,
  onNavigateToRequests,
  onNavigateToRequestCreate: _onNavigateToRequestCreate,
  onNavigateToAdmin,
  onNavigateToHierarchy,
  onNavigateToContractors,
  onNavigateToNormativeFiles,
  onNavigateToAdminCreate: _onNavigateToAdminCreate,
  onNavigateBackToRequests: _onNavigateBackToRequests,
  onSetContractorTab,
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
  const isAdminPage = pathname === '/admin';
  const isHierarchyPage = pathname === '/admin/hierarchy';
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
  const isSuperadminUsersPage = isSuperadmin && isAdminPage;
  const isSuperadminHierarchyPage = isSuperadmin && isHierarchyPage;
  const isAdminUsersPage = isAdmin && isAdminPage;
  const isAdminHierarchyPage = isAdmin && isHierarchyPage;
  const isSecurityOfficerContractorsPage = isSecurityOfficer && pathname.startsWith('/contractors');

  const isContractorRequestsArea =
    isContractor && (isRequestsListPage || isContractorRequestDetailsPage || isOfferWorkspacePage);
  const canUseContractorTabs = isContractorRequestsArea && canLoadOpenRequests && canLoadOfferedRequests;
  const isLeadRequestsTab = isLeadLike && (pathname.startsWith('/requests') || isOfferWorkspacePage);
  const isLeadEconomistsTab = isLeadLike && pathname.startsWith('/admin');
  const isLeadPlanTab = isLeadLike && pathname === '/pm-dashboard/plan';
  const isLeadDashboardTab =
    isEconomist
    && (
      (canViewDashboardProcess && pathname === '/pm-dashboard')
      || (canViewDashboardSavings && pathname === '/pm-dashboard/savings')
    );
  const hasEconomistDashboardNav = canViewDashboardProcess || canViewDashboardSavings || canViewDashboardPlans;
  const canUseLeadTabs = isLeadLike
    && !isProjectManager
    && !isLeadEconomist
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
    && (canViewDashboardProcess || canViewDashboardSavings || canViewDashboardPlans || canOpenUsersPage || canOpenHierarchyPage)
    && (
      isSuperadminDashboard
      || isSuperadminSavings
      || isSuperadminPlan
      || isSuperadminRequestsPage
      || isSuperadminUsersPage
      || isSuperadminHierarchyPage
      || isNormativeFilesPage
    );

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
    canOpenHierarchyPage,
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
        ...(canViewDashboardProcess ? [{ key: 'dashboard', value: 'dashboard', label: LABELS.dashboard }] : []),
        ...(canViewDashboardSavings ? [{ key: 'savings', value: 'savings', label: LABELS.savings }] : []),
        ...(canViewDashboardPlans ? [{ key: 'plan', value: 'plan', label: LABELS.plan }] : []),
        { key: 'requests', value: 'requests', label: LABELS.requests },
        ...(canOpenUsersPage ? [{ key: 'users', value: 'users', label: LABELS.users }] : []),
        ...(canOpenHierarchyPage ? [{ key: 'hierarchy', value: 'hierarchy', label: LABELS.hierarchy }] : []),
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
            : isSuperadminHierarchyPage
              ? 'hierarchy'
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
          if (value === 'hierarchy' && canOpenHierarchyPage) {
            onNavigateToHierarchy();
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
        canOpenHierarchyPage,
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
        canOpenHierarchyPage,
        canOpenContractorsPage,
        canViewDashboardProcess,
        canViewDashboardSavings,
        canViewDashboardPlans
      ),
      tabs: [
        ...(canViewDashboardProcess ? [{ key: 'dashboard', value: 'dashboard', label: LABELS.dashboard }] : []),
        ...(canViewDashboardSavings ? [{ key: 'savings', value: 'savings', label: LABELS.savings }] : []),
        ...(canViewDashboardPlans ? [{ key: 'plan', value: 'plan', label: LABELS.plan }] : []),
        { key: 'requests', value: 'requests', label: LABELS.requests },
        ...(canOpenUsersPage ? [{ key: 'employees', value: 'employees', label: LABELS.employees }] : []),
        ...(canOpenHierarchyPage ? [{ key: 'hierarchy', value: 'hierarchy', label: LABELS.hierarchy }] : []),
        ...(canOpenContractorsPage ? [{ key: 'contractors', value: 'contractors', label: LABELS.contractors }] : []),
      ],
      activeTab: isResponsibilityDashboard
        ? 'dashboard'
        : isResponsibilitySavings
          ? 'savings'
          : isResponsibilityPlan
            ? 'plan'
            : isHierarchyPage
                ? 'hierarchy'
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
        if (value === 'hierarchy' && canOpenHierarchyPage) {
          onNavigateToHierarchy();
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

  if (
    isRequestDetailsPage
    && !isSuperadmin
    && !canUseProjectManagerTabs
    && !canUseLeadTabs
    && !canUseEconomistTabs
    && !canUseOperatorTabs
  ) {
    return {
      mode: 'sidebar',
      breadcrumbs,
      tabs: [],
      actions: [],
      mobileNavItems: defaultMobileNavItems,
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
        { key: 'my', value: 'my', label: LABELS.myRequests },
        { key: 'open', value: 'open', label: LABELS.activeRequests },
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
        canOpenHierarchyPage,
        canOpenContractorsPage
      ),
      tabs: [
        ...(canViewDashboardProcess ? [{ key: 'dashboard', value: 'dashboard', label: LABELS.dashboard }] : []),
        ...(canViewDashboardSavings ? [{ key: 'savings', value: 'savings', label: LABELS.savings }] : []),
        ...(canViewDashboardPlans ? [{ key: 'plan', value: 'plan', label: LABELS.plan }] : []),
        { key: 'requests', value: 'requests', label: LABELS.requests },
        ...(canOpenUsersPage ? [{ key: 'economists', value: 'economists', label: LABELS.employees }] : []),
        ...(canOpenHierarchyPage ? [{ key: 'hierarchy', value: 'hierarchy', label: LABELS.hierarchy }] : []),
        ...(canOpenContractorsPage ? [{ key: 'contractors', value: 'contractors', label: LABELS.contractors }] : []),
      ],
      activeTab: isResponsibilityDashboard
        ? 'dashboard'
        : isResponsibilitySavings
          ? 'savings'
          : isResponsibilityPlan
            ? 'plan'
            : isHierarchyPage
                ? 'hierarchy'
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
        if (value === 'hierarchy' && canOpenHierarchyPage) {
          onNavigateToHierarchy();
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
        canOpenHierarchyPage,
        canOpenContractorsPage
      ),
      tabs: [
        ...(canViewDashboardProcess ? [{ key: 'dashboard', value: 'dashboard', label: LABELS.dashboard }] : []),
        ...(canViewDashboardSavings ? [{ key: 'savings', value: 'savings', label: LABELS.savings }] : []),
        ...(canViewDashboardPlans ? [{ key: 'plan', value: 'plan', label: LABELS.plan }] : []),
        { key: 'requests', value: 'requests', label: LABELS.requests },
        ...(canOpenUsersPage ? [{ key: 'economists', value: 'economists', label: LABELS.employees }] : []),
        ...(canOpenHierarchyPage ? [{ key: 'hierarchy', value: 'hierarchy', label: LABELS.hierarchy }] : []),
        ...(canOpenContractorsPage ? [{ key: 'contractors', value: 'contractors', label: LABELS.contractors }] : []),
      ],
      activeTab: isResponsibilityDashboard
        ? 'dashboard'
        : isResponsibilitySavings
          ? 'savings'
          : isResponsibilityPlan
            ? 'plan'
            : isHierarchyPage
                ? 'hierarchy'
              : pathname.startsWith('/admin')
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
        if (value === 'hierarchy' && canOpenHierarchyPage) {
          onNavigateToHierarchy();
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
      tabs: [{ key: 'requests', value: 'requests', label: LABELS.requests }],
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
      tabs: [{ key: 'contractors', value: 'contractors', label: LABELS.contractors }],
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

  if (isAdminUsersPage || isAdminHierarchyPage) {
    const tabs = [
      ...(canOpenUsersPage ? [{ key: 'users', value: 'users', label: LABELS.users }] : []),
      ...(canOpenHierarchyPage ? [{ key: 'hierarchy', value: 'hierarchy', label: LABELS.hierarchy }] : []),
    ];

    return {
      mode: 'sidebar',
      breadcrumbs,
      mobileNavItems: buildAdminMobileNavItems(canOpenUsersPage, canOpenHierarchyPage),
      tabs,
      activeTab: isAdminHierarchyPage ? 'hierarchy' : 'users',
      onTabChange: (value) => {
        if (value === 'users' && canOpenUsersPage) {
          onNavigateToAdmin();
          return;
        }
        if (value === 'hierarchy' && canOpenHierarchyPage) {
          onNavigateToHierarchy();
        }
      },
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
