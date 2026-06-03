import { render, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { AccountStatePage } from './AccountStatePage';

const useAuthMock = vi.fn();
const getRegistrationCurrentUserProfileMock = vi.fn();
const updateMyRegistrationProfileMock = vi.fn();
const updateMyRegistrationCompanyContactsMock = vi.fn();
const showErrorToastMock = vi.fn();
const showSuccessToastMock = vi.fn();
const logoutMock = vi.fn();

vi.mock('@app/providers/AuthProvider', () => ({
  useAuth: () => useAuthMock(),
}));

vi.mock('@shared/api/users/getCurrentUserProfile', () => ({
  getRegistrationCurrentUserProfile: () => getRegistrationCurrentUserProfileMock(),
  updateMyRegistrationProfile: (...args: unknown[]) => updateMyRegistrationProfileMock(...args),
  updateMyRegistrationCompanyContacts: (...args: unknown[]) => updateMyRegistrationCompanyContactsMock(...args),
}));

vi.mock('@shared/ui/toasts', () => ({
  useSystemToasts: () => ({
    showErrorToast: showErrorToastMock,
    showSuccessToast: showSuccessToastMock,
  }),
}));

const buildSession = (token: string) => ({
  token,
  tokenType: 'bearer',
  tokenExpiresAt: 1_700_000_000,
  userId: 'pegep95996',
  login: 'pegep95996',
  roleId: 3,
  role: 'contractor',
  status: 'review',
  authProvider: 'keycloak',
  businessAccess: false,
  onboardingState: null,
  permissions: [] as string[],
  appRoles: [] as string[],
  delegationRoles: [] as string[],
});

const profileResponse = {
  userId: 'pegep95996',
  roleId: 3,
  status: 'review',
  fullName: 'Иванов Иван',
  phone: '+79991234567',
  mail: 'pegep95996@aspensif.com',
  company: {
    companyName: 'ООО Ромашка',
    inn: '7707083893',
    phone: '+79990000000',
    mail: 'company@example.com',
    address: 'Москва',
    note: 'Тест',
  },
  unavailablePeriod: null,
  unavailablePeriods: [],
  permissions: [],
  keycloakRoles: [],
  appRoles: [],
  delegationRoles: [],
  actions: {
    view_profile: false,
    update_status: false,
    update_role: false,
    update_manager: false,
    manage_manual_contractor: false,
    manage_own_profile: true,
    manage_credentials: false,
    manage_company_contacts: true,
    manage_own_unavailability: false,
    manage_subordinate_unavailability: false,
  },
};

const renderPage = () => render(
  <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
    <AccountStatePage />
  </MemoryRouter>
);

describe('AccountStatePage refresh behavior', () => {
  beforeEach(() => {
    useAuthMock.mockReset();
    getRegistrationCurrentUserProfileMock.mockReset();
    updateMyRegistrationProfileMock.mockReset();
    updateMyRegistrationCompanyContactsMock.mockReset();
    showErrorToastMock.mockReset();
    showSuccessToastMock.mockReset();
    logoutMock.mockReset();

    getRegistrationCurrentUserProfileMock.mockResolvedValue(profileResponse);
  });

  it('does not refetch the registration profile when only the session token changes', async () => {
    useAuthMock.mockReturnValue({
      session: buildSession('token-1'),
      logout: logoutMock,
    });

    const view = renderPage();

    await waitFor(() => {
      expect(getRegistrationCurrentUserProfileMock).toHaveBeenCalledTimes(1);
    });

    useAuthMock.mockReturnValue({
      session: buildSession('token-2'),
      logout: logoutMock,
    });

    view.rerender(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <AccountStatePage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(getRegistrationCurrentUserProfileMock).toHaveBeenCalledTimes(1);
    });
  });
});
