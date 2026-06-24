import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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

const baseSession = {
  token: 'token',
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
};

const renderPage = () => render(
  <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
    <AccountStatePage />
  </MemoryRouter>
);

describe('AccountStatePage', () => {
  beforeEach(() => {
    useAuthMock.mockReset();
    getRegistrationCurrentUserProfileMock.mockReset();
    updateMyRegistrationProfileMock.mockReset();
    updateMyRegistrationCompanyContactsMock.mockReset();
    showErrorToastMock.mockReset();
    showSuccessToastMock.mockReset();
    logoutMock.mockReset();

    useAuthMock.mockReturnValue({
      session: baseSession,
      logout: logoutMock,
    });
  });

  it('renders Russian labels and decodes escaped registration draft values', async () => {
    getRegistrationCurrentUserProfileMock.mockResolvedValue({
      userId: 'pegep95996',
      roleId: 3,
      status: 'review',
      fullName: '\\u0418\\u0432\\u0430\\u043d\\u043e\\u0432 \\u0418\\u0432\\u0430\\u043d',
      phone: '+79991234567',
      mail: 'pegep95996@aspensif.com',
      company: {
        companyName: 'ООО Ромашка',
        inn: '\\u0037\\u0037\\u0030\\u0037\\u0030\\u0038\\u0033\\u0038\\u0039\\u0033',
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
        manage_contractor_unit_bindings: false,
        update_role: false,
        update_manager: false,
        manage_manual_contractor: false,
        manage_own_profile: true,
        manage_credentials: false,
        manage_company_contacts: true,
        manage_own_unavailability: false,
        manage_subordinate_unavailability: false,
      },
    });

    renderPage();

    expect(await screen.findByDisplayValue('Иванов Иван')).toBeInTheDocument();
    expect(screen.getByDisplayValue('7707083893')).toBeInTheDocument();
    expect(screen.getByText('Личные данные')).toBeInTheDocument();
    expect(screen.getByText('Данные компании')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Выйти' })).toBeInTheDocument();
    expect(screen.queryByText(/Статус:/i)).not.toBeInTheDocument();
  });

  it('shows required-field icons and closes the form after successful submit', async () => {
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
        manage_contractor_unit_bindings: false,
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
    getRegistrationCurrentUserProfileMock.mockResolvedValue(profileResponse);
    updateMyRegistrationProfileMock.mockResolvedValue(profileResponse);
    updateMyRegistrationCompanyContactsMock.mockResolvedValue(profileResponse);

    renderPage();

    await screen.findByDisplayValue('Иванов Иван');
    expect(screen.queryAllByTitle('Поле заполнено верно').length).toBeGreaterThanOrEqual(5);

    fireEvent.click(screen.getByRole('button', { name: 'Отправить данные' }));

    await waitFor(() => {
      expect(updateMyRegistrationProfileMock).toHaveBeenCalledTimes(1);
      expect(updateMyRegistrationCompanyContactsMock).toHaveBeenCalledTimes(1);
    });

    expect(screen.queryByDisplayValue('Иванов Иван')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Отправить данные' })).not.toBeInTheDocument();
  });
});
