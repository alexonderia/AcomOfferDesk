import { ThemeProvider } from '@mui/material/styles';
import type { ReactNode } from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ROLE } from '@shared/constants/roles';
import { appTheme } from '@shared/theme/appTheme';
import { ContractorsPage } from './ContractorsPage';

const setBreadcrumbActionsMock = vi.fn();
const listContractorsMock = vi.fn();
const listViewPropsMock = vi.fn();

vi.mock('@app/layouts/PageBreadcrumbActions', () => ({
  useSetPageBreadcrumbActions: (actions: ReactNode) => setBreadcrumbActionsMock(actions),
}));

vi.mock('@app/providers/AuthProvider', () => ({
  useAuth: () => ({
    session: {
      roleId: ROLE.PROJECT_MANAGER,
      permissions: ['contractors.manual.create', 'users.registration.invite'],
    },
  }),
}));

vi.mock('@shared/lib/responsive', () => ({
  useIsMobileViewport: () => true,
}));

vi.mock('@shared/api/contractors/listContractors', () => ({
  listContractors: (...args: unknown[]) => listContractorsMock(...args),
}));

vi.mock('@features/contractors/components/ContractorsListView', () => ({
  ContractorsListView: (props: unknown) => {
    listViewPropsMock(props);
    return <div data-testid="contractors-list" />;
  },
}));

vi.mock('@features/contractors/components/ContractorCreateDialog', () => ({
  ContractorCreateDialog: () => null,
}));

vi.mock('@features/contractors/components/ContractorInviteDialog', () => ({
  ContractorInviteDialog: () => null,
}));

describe('ContractorsPage', () => {
  beforeEach(() => {
    setBreadcrumbActionsMock.mockReset();
    listContractorsMock.mockReset();
    listViewPropsMock.mockReset();
    listContractorsMock.mockResolvedValue([]);
  });

  it('uses icon-only invite action on mobile', async () => {
    render(
      <ThemeProvider theme={appTheme}>
        <ContractorsPage />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(setBreadcrumbActionsMock).toHaveBeenCalled();
    });

    const breadcrumbAction = setBreadcrumbActionsMock.mock.calls.at(-1)?.[0];
    expect(breadcrumbAction).toBeTruthy();

    render(<ThemeProvider theme={appTheme}>{breadcrumbAction}</ThemeProvider>);

    const inviteButton = screen.getByRole('button', { name: 'Пригласить' });
    expect(inviteButton).toBeInTheDocument();
    expect(inviteButton).toHaveTextContent('');
    expect(inviteButton).toHaveClass('MuiButton-outlined');
    expect(screen.queryByText('Пригласить')).not.toBeInTheDocument();
  });

  it('renders contractors list and forwards add action', async () => {
    render(
      <ThemeProvider theme={appTheme}>
        <ContractorsPage />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(listContractorsMock).toHaveBeenCalled();
    });

    expect(screen.getByTestId('contractors-list')).toBeInTheDocument();

    const listViewProps = listViewPropsMock.mock.calls.at(-1)?.[0] as {
      onAddClick?: () => void;
    };
    expect(typeof listViewProps.onAddClick).toBe('function');
  });
});
