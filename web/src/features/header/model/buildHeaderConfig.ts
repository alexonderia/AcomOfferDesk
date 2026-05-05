import type { HeaderConfig, HeaderMobileNavItem, HeaderSidebarItem } from './types';
import { ROLE } from '@shared/constants/roles';

type BuildHeaderConfigArgs = {
  roleId: number | null;
  pathname: string;
  canCreateRequest: boolean;
  canRegisterUser: boolean;
  canLoadOpenRequests: boolean;
  canLoadOfferedRequests: boolean;
  canOpenUsersPage: boolean;
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

const superadminItems: HeaderSidebarItem[] = [
  { key: 'users', label: 'Пользователи', to: '/admin' },
  { key: 'requests', label: 'Заявки', to: '/requests' },
  { key: 'offers', label: 'КП', disabled: true },
  { key: 'roles', label: 'Роли', disabled: true },
  { key: 'contact', label: 'Обратная связь', to: '/feedback', isBottomItem: true },
  { key: 'logout', label: 'Выйти', isBottomItem: true },
];

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

const buildSuperadminMobileNavItems = (): HeaderMobileNavItem[] => [
  { key: 'users', label: 'Пользователи', to: '/admin' },
  { key: 'requests', label: 'Заявки', to: '/requests' },
  buildMoreNavItem({
    showProfile: false,
    showNormative: false,
    showRoleGuide: true,
    showFeedback: true,
    showLogout: true,
  }),
];

const buildProjectManagerMobileNavItems = (showNormative: boolean, canOpenUsersPage: boolean): HeaderMobileNavItem[] => {
  const items: HeaderMobileNavItem[] = [
    {
      key: 'dashboard',
      label: 'Дашборд',
      to: '/pm-dashboard',
      children: [
        { key: 'dashboard-process', label: 'Процесс работы', to: '/pm-dashboard' },
        { key: 'dashboard-savings', label: 'Экономия', to: '/pm-dashboard/savings' },
        { key: 'dashboard-plan', label: 'План', to: '/pm-dashboard/plan' },
      ],
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

const buildLeadMobileNavItems = (): HeaderMobileNavItem[] => [
  {
    key: 'dashboard',
    label: 'Дашборд',
    to: '/pm-dashboard/plan',
    children: [
      { key: 'dashboard-plan', label: 'План', to: '/pm-dashboard/plan' },
    ],
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
  isAdmin,
  canOpenUsersPage,
}: {
  isSuperadmin: boolean;
  isProjectManager: boolean;
  isLeadEconomist: boolean;
  isContractor: boolean;
  isLeadLike: boolean;
  isAdmin: boolean;
  canOpenUsersPage: boolean;
}): HeaderMobileNavItem[] => {
  if (isSuperadmin) {
    return buildSuperadminMobileNavItems();
  }

  if (isProjectManager || isLeadEconomist) {
    return buildProjectManagerMobileNavItems(isLeadEconomist, canOpenUsersPage);
  }

  if (isContractor) {
    return buildContractorMobileNavItems();
  }

  if (isLeadLike && !isProjectManager && !isLeadEconomist) {
    return buildLeadMobileNavItems();
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
  const isLeadLike = isLeadEconomist || isProjectManager || isEconomist;

  const isRequestsListPage = pathname === '/requests';
  const isRequestDetailsPage = /^\/requests\/\d+$/.test(pathname);
  const isContractorRequestDetailsPage = /^\/requests\/\d+\/contractor$/.test(pathname);
  const isOfferWorkspacePage = /^\/offers\/\d+\/workspace$/.test(pathname);
  const isResponsibilityDashboard = (isProjectManager || isLeadEconomist) && pathname === '/pm-dashboard';
  const isResponsibilitySavings = (isProjectManager || isLeadEconomist) && pathname === '/pm-dashboard/savings';
  const isResponsibilityPlan = (isProjectManager || isLeadEconomist || isEconomist) && pathname === '/pm-dashboard/plan';
  const isResponsibilityRequestsPage =
    (isProjectManager || isLeadEconomist) && (pathname.startsWith('/requests') || isOfferWorkspacePage);
  const isResponsibilityEmployeesPage = (isProjectManager || isLeadEconomist) && pathname.startsWith('/admin');
  const isAdminUsersPage = isAdmin && pathname.startsWith('/admin');

  const isContractorRequestsArea = isContractor
    && (isRequestsListPage || isContractorRequestDetailsPage || isOfferWorkspacePage);
  const canUseContractorTabs = isContractorRequestsArea && canLoadOpenRequests && canLoadOfferedRequests;
  const isLeadRequestsTab = isLeadLike && (pathname.startsWith('/requests') || isOfferWorkspacePage);
  const isLeadEconomistsTab = isLeadLike && pathname.startsWith('/admin');
  const isLeadPlanTab = isLeadLike && pathname === '/pm-dashboard/plan';
  const canUseLeadTabs = isLeadLike && !isProjectManager && !isLeadEconomist
    && (isLeadRequestsTab || isLeadEconomistsTab || isLeadPlanTab)
    && (canOpenUsersPage || isEconomist);
  const canUseProjectManagerTabs = (isProjectManager || isLeadEconomist)
    && (isResponsibilityDashboard || isResponsibilitySavings || isResponsibilityPlan || isResponsibilityRequestsPage || isResponsibilityEmployeesPage)
    && canOpenUsersPage;

  const defaultMobileNavItems = resolveDefaultMobileNavItems({
    isSuperadmin,
    isProjectManager,
    isLeadEconomist,
    isContractor,
    isLeadLike,
    isAdmin,
    canOpenUsersPage,
  });

  if (isSuperadmin) {
    return {
      mode: 'sidebar',
      tabs: [],
      actions: [],
      breadcrumbs,
      sidebarItems: superadminItems,
      mobileNavItems: buildSuperadminMobileNavItems(),
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
      mobileNavItems: buildProjectManagerMobileNavItems(isLeadEconomist, canOpenUsersPage),
      tabs: [
        { key: 'dashboard', value: 'dashboard', label: 'Дашборд' },
        { key: 'savings', value: 'savings', label: 'Экономия' },
        { key: 'plan', value: 'plan', label: 'План' },
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
        if (value === 'dashboard') {
          onNavigateToDashboard();
          return;
        }
        if (value === 'savings') {
          onNavigateToSavings();
          return;
        }
        if (value === 'plan') {
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
      mobileNavItems: buildLeadMobileNavItems(),
      tabs: [
        { key: 'dashboard', value: 'dashboard', label: 'Дашборд' },
        { key: 'plan', value: 'plan', label: 'План' },
        { key: 'requests', value: 'requests', label: 'Заявки' },
        { key: 'economists', value: 'economists', label: 'Экономисты' }
      ],
      activeTab: pathname === '/pm-dashboard/plan' ? 'plan' : pathname === '/admin' ? 'economists' : 'requests',
      onTabChange: (value) => {
        if (value === 'dashboard' || value === 'plan') {
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
