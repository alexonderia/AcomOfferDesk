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
  canCreateNormativeFile: false,
  canViewFeedback: false,
  canViewDashboardProcess: false,
  canViewDashboardSavings: false,
  canViewDashboardPlans: false,
  breadcrumbs: [],
  contractorTab: 'my' as const,
  adminUsersTab: 'contractors' as const,
  onNavigateToDashboard: vi.fn(),
  onNavigateToSavings: vi.fn(),
  onNavigateToPlan: vi.fn(),
  onNavigateToRequests: vi.fn(),
  onNavigateToRequestCreate: vi.fn(),
  onNavigateToAdmin: vi.fn(),
  onNavigateToAdminCreate: vi.fn(),
  onNavigateBackToRequests: vi.fn(),
  onSetContractorTab: vi.fn(),
  onSetAdminUsersTab: vi.fn(),
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
      canViewDashboardProcess: true,
      canViewDashboardSavings: true,
      canViewDashboardPlans: true,
    });

    expect(tabKeys(config)).toEqual(['dashboard', 'savings', 'plan', 'requests', 'users']);
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
  });

  it('hides admin section when users permission is missing', () => {
    const config = buildHeaderConfig({
      ...baseArgs(),
      roleId: ROLE.ECONOMIST,
      canOpenUsersPage: false,
    });

    expect(tabKeys(config)).toEqual([]);
    expect(mobileKeys(config)).not.toContain('economists');
    expect(mobileKeys(config)).not.toContain('users');
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
});
