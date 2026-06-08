import { act, renderHook, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { PropsWithChildren } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ROLE } from '@shared/constants/roles';
import { useAdminPage } from './useAdminPage';

const useAuthMock = vi.fn();
const getUsersMock = vi.fn();
const getManagerCandidatesMock = vi.fn();
const registerUserMock = vi.fn();
const createManualContractorMock = vi.fn();
const showErrorToastMock = vi.fn();
const showSuccessToastMock = vi.fn();

vi.mock('@app/providers/AuthProvider', () => ({
  useAuth: () => useAuthMock(),
}));

vi.mock('@shared/api/users/getUsers', () => ({
  getUsers: (...args: unknown[]) => getUsersMock(...args),
}));

vi.mock('@shared/api/users/getManagerCandidates', () => ({
  getManagerCandidates: (...args: unknown[]) => getManagerCandidatesMock(...args),
}));

vi.mock('@shared/api/auth/registerUser', () => ({
  registerUser: (...args: unknown[]) => registerUserMock(...args),
}));

vi.mock('@shared/api/users/createManualContractor', () => ({
  createManualContractor: (...args: unknown[]) => createManualContractorMock(...args),
}));

vi.mock('@shared/ui/toasts', () => ({
  useSystemToasts: () => ({
    showErrorToast: showErrorToastMock,
    showSuccessToast: showSuccessToastMock,
  }),
}));

const baseSession = {
  roleId: ROLE.SUPERADMIN,
  permissions: [
    'users.create',
    'contractors.manual.create',
    'users.role.update_any',
    'users.status.update',
  ],
};

const wrapper = ({ children }: PropsWithChildren) => (
  <MemoryRouter
    initialEntries={['/admin?users_tab=contractors']}
    future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
  >
    {children}
  </MemoryRouter>
);

describe('useAdminPage', () => {
  beforeEach(() => {
    useAuthMock.mockReset();
    getUsersMock.mockReset();
    getManagerCandidatesMock.mockReset();
    registerUserMock.mockReset();
    createManualContractorMock.mockReset();
    showErrorToastMock.mockReset();
    showSuccessToastMock.mockReset();

    useAuthMock.mockReturnValue({ session: baseSession });
    getUsersMock.mockResolvedValue({ items: [] });
    getManagerCandidatesMock.mockResolvedValue({ items: [] });
  });

  it('opens the create dialog with the security officer role on the security tab for superadmin', async () => {
    const { result } = renderHook(() => useAdminPage(), { wrapper });

    await waitFor(() => expect(result.current.activeTab).toBe('contractors'));
    expect(result.current.form.getValues('role_id')).toBe(ROLE.CONTRACTOR);

    act(() => {
      result.current.handleTabChange('security_officers');
    });

    await waitFor(() => expect(result.current.activeTab).toBe('security_officers'));
    await waitFor(() => expect(result.current.roleOptions[0]?.id).toBe(ROLE.SECURITY_OFFICER));

    act(() => {
      result.current.openCreateDialog();
    });

    expect(result.current.form.getValues('role_id')).toBe(ROLE.SECURITY_OFFICER);
    expect(result.current.isContractorRole).toBe(false);
  });
});
