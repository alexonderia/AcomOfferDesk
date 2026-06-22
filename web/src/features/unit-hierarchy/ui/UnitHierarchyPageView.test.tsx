import { ThemeProvider } from '@mui/material/styles';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { appTheme } from '@shared/theme/appTheme';
import { UnitHierarchyPageView } from './UnitHierarchyPageView';

const useUnitHierarchyPageMock = vi.fn();

vi.mock('../model/useUnitHierarchyPage', () => ({
  useUnitHierarchyPage: () => useUnitHierarchyPageMock(),
}));

const buildViewState = () => ({
  tree: [
    {
      unit_id: 11,
      name: 'Финансовый блок',
      id_parent: null,
      is_active: true,
      members: [],
      children: [],
      actions: {
        canCreateChild: true,
        canUpdate: true,
        canDeactivate: true,
        canManageMembers: true,
      },
    },
  ],
  recommendedTree: [
    {
      user_id: 'chief-1',
      full_name: 'Ахметшин Ренат Габдельфатович',
      role_id: 1,
      role_name: 'Главный специалист',
      status: 'active',
      id_parent_user: null,
      children: [
        {
          user_id: 'lead-1',
          full_name: 'Рахматуллин Асхат Ирекович',
          role_id: 2,
          role_name: 'Ведущий специалист',
          status: 'active',
          id_parent_user: 'chief-1',
          children: [],
        },
      ],
    },
  ],
  isLoading: false,
  error: null,
  recommendedError: null,
  canCreateRootUnit: true,
  unitDialogMode: null,
  activeUnit: null,
  unitName: '',
  setUnitName: vi.fn(),
  isSavingUnit: false,
  isMemberDialogOpen: false,
  availableUsers: [],
  selectedUserId: '',
  setSelectedUserId: vi.fn(),
  memberSearch: '',
  setMemberSearch: vi.fn(),
  isLoadingUsers: false,
  isSavingMember: false,
  openCreateRootDialog: vi.fn(),
  openCreateChildDialog: vi.fn(),
  openRenameDialog: vi.fn(),
  closeUnitDialog: vi.fn(),
  submitUnit: vi.fn(),
  deactivateUnit: vi.fn(),
  openMemberDialog: vi.fn(),
  closeMemberDialog: vi.fn(),
  submitMember: vi.fn(),
  deleteMember: vi.fn(),
});

const renderView = () => render(
  <ThemeProvider theme={appTheme}>
    <UnitHierarchyPageView />
  </ThemeProvider>
);

describe('UnitHierarchyPageView', () => {
  beforeEach(() => {
    useUnitHierarchyPageMock.mockReset();
    useUnitHierarchyPageMock.mockReturnValue(buildViewState());
  });

  it('renders the recommended hierarchy as a tree chart without hiding editable units', () => {
    renderView();

    expect(screen.getByText('Рекомендуемая структура')).toBeInTheDocument();
    expect(screen.getByText('Ахметшин Ренат Габдельфатович')).toBeInTheDocument();
    expect(screen.getByText('Рахматуллин Асхат Ирекович')).toBeInTheDocument();
    expect(screen.getByText('Корневой узел')).toBeInTheDocument();
    expect(screen.getByText('chief-1')).toBeInTheDocument();
    expect(screen.getByText('Финансовый блок')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Создать подразделение' })).toBeInTheDocument();
  });
});
