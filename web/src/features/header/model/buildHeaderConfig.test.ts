import { describe, expect, it, vi } from 'vitest';
import { ROLE } from '@shared/constants/roles';
import { buildHeaderConfig } from './buildHeaderConfig';

const baseArgs = () => ({
  roleId: null as number | null,
  pathname: '/requests',
  canCreateRequest: false,
  canRegisterUser: false,
  canLoadOpenRequests: false,
  canLoadOfferedRequests: false,
  canOpenUsersPage: false,
  canOpenHierarchyPage: false,
  canOpenContractorsPage: false,
  canManageNormativeFiles: false,
  canViewFeedback: false,
  canViewDashboardProcess: false,
  canViewDashboardSavings: false,
  canViewDashboardPlans: false,
  breadcrumbs: [],
  contractorTab: 'my' as const,
  onNavigateToDashboard: vi.fn(),
  onNavigateToSavings: vi.fn(),
  onNavigateToPlan: vi.fn(),
  onNavigateToRequests: vi.fn(),
  onNavigateToRequestCreate: vi.fn(),
  onNavigateToAdmin: vi.fn(),
  onNavigateToHierarchy: vi.fn(),
  onNavigateToContractors: vi.fn(),
  onNavigateToNormativeFiles: vi.fn(),
  onNavigateToAdminCreate: vi.fn(),
  onNavigateBackToRequests: vi.fn(),
  onSetContractorTab: vi.fn(),
});

const mobileKeys = (config: ReturnType<typeof buildHeaderConfig>) =>
  (config.mobileNavItems ?? []).map((item) => item.key);

const tabKeys = (config: ReturnType<typeof buildHeaderConfig>) => config.tabs.map((tab) => tab.key);

describe('buildHeaderConfig role navigation', () => {
  it('shows all major sections for superadmin', () => {
    const config = buildHeaderConfig({
      ...baseArgs(),
      roleId: ROLE.SUPERADMIN,
      canOpenUsersPage: true,
      canOpenHierarchyPage: true,
      canViewDashboardProcess: true,
      canViewDashboardSavings: true,
      canViewDashboardPlans: true,
    });

    expect(tabKeys(config)).toEqual(['dashboard', 'savings', 'plan', 'requests', 'users', 'hierarchy']);
  });

  it('shows dashboard tabs only for granted split-permissions', () => {
    const processOnly = buildHeaderConfig({
      ...baseArgs(),
      roleId: ROLE.SUPERADMIN,
      canOpenUsersPage: true,
      canViewDashboardProcess: true,
      canViewDashboardSavings: false,
      canViewDashboardPlans: false,
    });
    const savingsOnly = buildHeaderConfig({
      ...baseArgs(),
      roleId: ROLE.SUPERADMIN,
      canOpenUsersPage: true,
      canViewDashboardProcess: false,
      canViewDashboardSavings: true,
      canViewDashboardPlans: false,
    });
    const planOnly = buildHeaderConfig({
      ...baseArgs(),
      roleId: ROLE.SUPERADMIN,
      canOpenUsersPage: true,
      canViewDashboardProcess: false,
      canViewDashboardSavings: false,
      canViewDashboardPlans: true,
    });

    expect(tabKeys(processOnly)).toEqual(['dashboard', 'requests', 'users']);
    expect(tabKeys(savingsOnly)).toEqual(['savings', 'requests', 'users']);
    expect(tabKeys(planOnly)).toEqual(['plan', 'requests', 'users']);
  });

  it('hides dashboard tabs for economist without dashboard permissions', () => {
    const config = buildHeaderConfig({
      ...baseArgs(),
      roleId: ROLE.ECONOMIST,
      canOpenUsersPage: true,
      canViewDashboardProcess: false,
      canViewDashboardSavings: false,
      canViewDashboardPlans: false,
    });

    expect(tabKeys(config)).toEqual(['requests', 'economists']);
    expect(tabKeys(config)).not.toContain('dashboard');
    expect(mobileKeys(config)).not.toContain('dashboard');
    expect(mobileKeys(config)).toContain('employees');
  });

  it('shows plan dashboard section for economist with plans permission', () => {
    const config = buildHeaderConfig({
      ...baseArgs(),
      roleId: ROLE.ECONOMIST,
      canOpenUsersPage: true,
      canViewDashboardProcess: false,
      canViewDashboardSavings: false,
      canViewDashboardPlans: true,
    });

    expect(tabKeys(config)).toEqual(['plan', 'requests', 'economists']);
    expect(mobileKeys(config)).toContain('dashboard');
  });

  it('shows process and savings dashboard tabs for economist with module statistics permissions', () => {
    const config = buildHeaderConfig({
      ...baseArgs(),
      roleId: ROLE.ECONOMIST,
      canOpenUsersPage: true,
      canOpenContractorsPage: true,
      canViewDashboardProcess: true,
      canViewDashboardSavings: true,
      canViewDashboardPlans: true,
    });

    expect(tabKeys(config)).toEqual(['dashboard', 'savings', 'plan', 'requests', 'economists', 'contractors']);
    expect(mobileKeys(config)).toContain('dashboard');
    expect(mobileKeys(config)).toContain('employees');
    expect(mobileKeys(config)).not.toContain('contractors');
    const dashboardNav = config.mobileNavItems?.find((item) => item.key === 'dashboard');
    expect(dashboardNav?.children?.map((child) => child.key)).toEqual(
      expect.arrayContaining(['dashboard-process', 'dashboard-savings', 'dashboard-plan'])
    );
    const moreNav = config.mobileNavItems?.find((item) => item.key === 'more');
    expect(moreNav?.children?.map((child) => child.key)).toEqual(
      expect.arrayContaining(['contractors'])
    );
  });

  it('highlights hierarchy tab for project manager on hierarchy page', () => {
    const config = buildHeaderConfig({
      ...baseArgs(),
      roleId: ROLE.PROJECT_MANAGER,
      pathname: '/admin/hierarchy',
      canOpenUsersPage: true,
      canOpenHierarchyPage: true,
      canViewDashboardProcess: true,
    });

    expect(tabKeys(config)).toEqual(['dashboard', 'requests', 'employees', 'hierarchy']);
    expect(config.activeTab).toBe('hierarchy');
  });

  it('highlights hierarchy tab for economist on hierarchy page', () => {
    const config = buildHeaderConfig({
      ...baseArgs(),
      roleId: ROLE.ECONOMIST,
      pathname: '/admin/hierarchy',
      canOpenUsersPage: true,
      canOpenHierarchyPage: true,
      canViewDashboardPlans: true,
    });

    expect(tabKeys(config)).toEqual(['plan', 'requests', 'economists', 'hierarchy']);
    expect(config.activeTab).toBe('hierarchy');
  });

  it('hides admin section when users permission is missing', () => {
    const config = buildHeaderConfig({
      ...baseArgs(),
      roleId: ROLE.ECONOMIST,
      canOpenUsersPage: false,
    });

    expect(tabKeys(config)).toEqual([]);
    expect(mobileKeys(config)).not.toContain('economists');
    expect(mobileKeys(config)).not.toContain('employees');
  });

  it('shows contractors as a top-level mobile item for project manager navigation', () => {
    const config = buildHeaderConfig({
      ...baseArgs(),
      roleId: ROLE.PROJECT_MANAGER,
      canOpenUsersPage: true,
      canOpenContractorsPage: true,
      canManageNormativeFiles: true,
      canViewDashboardProcess: true,
      canViewDashboardSavings: true,
      canViewDashboardPlans: true,
    });

    expect(mobileKeys(config)).toEqual(['dashboard', 'requests', 'employees', 'more']);
    const moreNav = config.mobileNavItems?.find((item) => item.key === 'more');
    expect(moreNav?.children?.map((child) => child.key)).toEqual(
      expect.arrayContaining(['contractors', 'normative'])
    );
  });

  it('shows a separate contractors tab for economist on the contractors page', () => {
    const config = buildHeaderConfig({
      ...baseArgs(),
      roleId: ROLE.ECONOMIST,
      pathname: '/contractors',
      canOpenUsersPage: true,
      canOpenContractorsPage: true,
      canViewDashboardProcess: true,
      canViewDashboardSavings: true,
      canViewDashboardPlans: true,
    });

    expect(tabKeys(config)).toEqual(['dashboard', 'savings', 'plan', 'requests', 'economists', 'contractors']);
    expect(config.activeTab).toBe('contractors');
    expect(mobileKeys(config)).toContain('dashboard');
    expect(mobileKeys(config)).toContain('employees');
    expect(mobileKeys(config)).toContain('more');
  });

  it('shows contractor-specific request/workspace tabs for contractor', () => {
    const config = buildHeaderConfig({
      ...baseArgs(),
      roleId: ROLE.CONTRACTOR,
      pathname: '/offers/22/workspace',
      canLoadOpenRequests: true,
      canLoadOfferedRequests: true,
    });

    expect(tabKeys(config)).toEqual(['my', 'open']);
    expect(mobileKeys(config)).toContain('requests');
    expect(mobileKeys(config)).not.toContain('admin');
  });

  it('shows only contractors navigation for security officer', () => {
    const config = buildHeaderConfig({
      ...baseArgs(),
      roleId: ROLE.SECURITY_OFFICER,
      pathname: '/contractors',
      canOpenContractorsPage: true,
    });

    expect(tabKeys(config)).toEqual(['contractors']);
    expect(config.activeTab).toBe('contractors');
    expect(mobileKeys(config)).toEqual(['contractors', 'more']);
  });

  it('shows only users tab for admin', () => {
    const config = buildHeaderConfig({
      ...baseArgs(),
      roleId: ROLE.ADMIN,
      pathname: '/admin',
      canOpenUsersPage: true,
    });

    expect(tabKeys(config)).toEqual(['users']);
    expect(config.activeTab).toBe('users');

    const usersNav = config.mobileNavItems?.find((item) => item.key === 'users');
    expect(usersNav?.label).toBe('Пользователи');
    expect(usersNav?.children).toBeUndefined();
  });

  it('shows hierarchy navigation for admin when units.read is granted', () => {
    const config = buildHeaderConfig({
      ...baseArgs(),
      roleId: ROLE.ADMIN,
      pathname: '/admin/hierarchy',
      canOpenHierarchyPage: true,
    });

    expect(tabKeys(config)).toEqual(['hierarchy']);
    expect(config.activeTab).toBe('hierarchy');
    expect(mobileKeys(config)).toEqual(['hierarchy', 'more']);
  });

  it('shows only requests section for operator', () => {
    const config = buildHeaderConfig({
      ...baseArgs(),
      roleId: ROLE.OPERATOR,
      pathname: '/requests',
    });

    expect(tabKeys(config)).toEqual(['requests']);
    expect(mobileKeys(config)).toContain('requests');
    expect(tabKeys(config)).not.toEqual(expect.arrayContaining(['dashboard', 'users', 'offers', 'chat']));
  });

  it('keeps request tabs on the request details page without a back action', () => {
    const config = buildHeaderConfig({
      ...baseArgs(),
      roleId: ROLE.ECONOMIST,
      pathname: '/requests/er',
      canOpenUsersPage: true,
      canViewDashboardProcess: true,
      canViewDashboardSavings: true,
      canViewDashboardPlans: true,
    });

    expect(tabKeys(config)).toEqual(['dashboard', 'savings', 'plan', 'requests', 'economists']);
    expect(config.activeTab).toBe('requests');
    expect(config.backAction).toBeUndefined();
  });

  it('does not highlight requests tab on normative files page', () => {
    const config = buildHeaderConfig({
      ...baseArgs(),
      roleId: ROLE.LEAD_ECONOMIST,
      pathname: '/normative-files',
      canManageNormativeFiles: true,
      canOpenUsersPage: true,
      canOpenContractorsPage: true,
      canViewDashboardProcess: true,
    });

    expect(config.activeTab).toBe('normative');
    expect(config.normativeFilesActive).toBe(true);
    expect(config.tabs.some((tab) => tab.value === config.activeTab)).toBe(false);
  });
});
