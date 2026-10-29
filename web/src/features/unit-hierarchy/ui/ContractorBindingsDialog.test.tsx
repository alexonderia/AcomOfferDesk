import { ThemeProvider } from '@mui/material/styles';
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { appTheme } from '@shared/theme/appTheme';
import { ContractorBindingsDialog } from './ContractorBindingsDialog';

const useAuthMock = vi.fn();
const listContractorsTableMock = vi.fn();
const getUsersMock = vi.fn();
const getContractorRootUnitsMock = vi.fn();

vi.mock('@app/providers/AuthProvider', () => ({
  useAuth: () => useAuthMock(),
}));

vi.mock('@shared/api/contractors/listContractors', () => ({
  listContractorsTable: (...args: unknown[]) => listContractorsTableMock(...args),
}));

vi.mock('@shared/api/users/getUsers', () => ({
  getUsers: (...args: unknown[]) => getUsersMock(...args),
}));

vi.mock('@shared/api/contractors/getContractorRootUnits', () => ({
  getContractorRootUnits: (...args: unknown[]) => getContractorRootUnitsMock(...args),
}));

vi.mock('@shared/ui/toasts', () => ({
  useSystemToasts: () => ({
    showSystemToast: vi.fn(),
    showErrorToast: vi.fn(),
  }),
  useToastMessageEffect: vi.fn(),
}));

const renderDialog = () => render(
  <ThemeProvider theme={appTheme}>
    <ContractorBindingsDialog
      open
      departmentName="УЭ"
      onClose={() => {}}
      onSaved={() => {}}
    />
  </ThemeProvider>
);

describe('ContractorBindingsDialog', () => {
  beforeEach(() => {
    useAuthMock.mockReset();
    listContractorsTableMock.mockReset();
    getUsersMock.mockReset();
    getContractorRootUnitsMock.mockReset();
  });

  it('loads contractors via users api fallback when contractors.read is missing', async () => {
    useAuthMock.mockReturnValue({
      session: {
        roleId: 2,
        permissions: ['users.read', 'users.status.update'],
      },
    });
    getUsersMock.mockResolvedValue({
      items: [
        {
          user_id: 'contractor-1',
          role_id: 3,
          id_parent: null,
          status: 'Активен',
          full_name: 'Контрагент 1',
          phone: null,
          mail: 'contractor-1@example.com',
          company_name: 'ООО Ромашка',
          inn: null,
          company_phone: null,
          company_mail: null,
          address: null,
          note: null,
          actions: {
            view: false,
            updateStatus: false,
            manageContractorUnitBindings: true,
            updateRole: false,
            updateManager: false,
            manageSubordinateUnavailability: false,
            manageManualContractor: false,
          },
        },
      ],
    });
    getContractorRootUnitsMock.mockResolvedValue({
      contractorUserId: 'contractor-1',
      canManage: true,
      items: [
        {
          unitId: 1,
          unitName: 'УЭ',
          isBound: true,
          canManage: true,
        },
      ],
    });

    renderDialog();

    await waitFor(() => expect(getUsersMock).toHaveBeenCalledWith(3));
    expect(listContractorsTableMock).not.toHaveBeenCalled();
    await waitFor(() => expect(getContractorRootUnitsMock).toHaveBeenCalledWith('contractor-1'));
    expect(screen.getByText('contractor-1')).toBeInTheDocument();
    expect(screen.getByText('УЭ')).toBeInTheDocument();
  });
});
