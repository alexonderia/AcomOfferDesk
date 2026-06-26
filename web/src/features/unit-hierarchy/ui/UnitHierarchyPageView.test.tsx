import { ThemeProvider } from '@mui/material/styles';
import { fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { appTheme } from '@shared/theme/appTheme';
import { UnitHierarchyPageView } from './UnitHierarchyPageView';

const useUnitHierarchyPageMock = vi.fn();

vi.mock('../model/useUnitHierarchyPage', () => ({
  useUnitHierarchyPage: () => useUnitHierarchyPageMock(),
}));

const baseDepartment = {
  unit_id: 1,
  name: 'Финансовый блок',
  id_parent: null,
  is_active: true,
  members: [],
  children: [
    {
      unit_id: 2,
      name: 'Проект А',
      id_parent: 1,
      is_active: true,
      members: [
        {
          user_id: 'econ-1',
          full_name: 'Экономист 1',
          role_id: 6,
          role_name: 'Экономист',
          status: 'active',
        },
      ],
      children: [
        {
          unit_id: 3,
          name: 'Лист 1',
          id_parent: 2,
          is_active: true,
          members: [],
          children: [],
          actions: {
            canCreateChild: true,
            canUpdate: true,
            canDelete: true,
            canManageMembers: true,
          },
        },
      ],
      actions: {
        canCreateChild: true,
        canUpdate: true,
        canDelete: true,
        canManageMembers: true,
      },
    },
  ],
  actions: {
    canCreateChild: true,
    canUpdate: true,
    canDelete: false,
    canManageMembers: true,
  },
};

const buildViewState = (): any => ({
  tree: [baseDepartment],
  departments: [baseDepartment],
  isLoading: false,
  error: null,
  selectedDepartment: baseDepartment,
  selectedDepartmentId: 1,
  setSelectedDepartmentId: vi.fn(),
  selectedEditorUnitId: null,
  setSelectedEditorUnitId: vi.fn(),
  editorRootUnit: null,
  departmentStaff: [
    {
      user_id: 'econ-1',
      full_name: 'Экономист 1',
      role_id: 6,
      role_name: 'Экономист',
      status: 'active',
    },
  ],
  departmentContractors: [],
  selectedDepartmentUnitOptions: [
    { unitId: 1, label: 'Финансовый блок' },
    { unitId: 2, label: 'Финансовый блок / Проект А' },
    { unitId: 3, label: 'Финансовый блок / Проект А / Лист 1' },
  ],
  canCreateRootUnit: true,
  activeUnitDetails: null,
  activeUnitParent: null,
  activeUnitPathLabel: '',
  setActiveUnitDetailsId: vi.fn(),
  unitDialogState: { mode: null, unit: null },
  isSavingUnit: false,
  editableParentOptions: [],
  openCreateRootDialog: vi.fn(),
  openCreateChildDialog: vi.fn(),
  openEditUnitDialog: vi.fn(),
  closeUnitDialog: vi.fn(),
  submitUnit: vi.fn(),
  memberDialogState: { unit: null, search: '', selectedUserId: '' },
  setMemberDialogState: vi.fn(),
  availableUsers: [],
  isLoadingUsers: false,
  isSavingMember: false,
  openMemberDialog: vi.fn(),
  closeMemberDialog: vi.fn(),
  submitMember: vi.fn(),
  removeMemberFromUnit: vi.fn(),
  contractorDialogUnit: null,
  openContractorDialog: vi.fn(),
  closeContractorDialog: vi.fn(),
  removeContractorFromUnit: vi.fn(),
  moveMemberState: null,
  moveUnitOptions: [],
  setMoveMemberState: vi.fn(),
  isMovingMember: false,
  openMoveMemberDialog: vi.fn(),
  closeMoveMemberDialog: vi.fn(),
  submitMoveMember: vi.fn(),
  deleteDialogState: null,
  isDeletingUnit: false,
  openDeleteDialog: vi.fn(),
  closeDeleteDialog: vi.fn(),
  confirmDeleteUnit: vi.fn(),
  loadTree: vi.fn(),
  findRootUnitForUnit: vi.fn(() => baseDepartment),
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

  it('renders department graphs with second-level unit blocks and staff tree', () => {
    renderView();

    expect(screen.getByText('Подразделения и объединения')).toBeInTheDocument();
    expect(screen.getAllByText('Финансовый блок').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Проект А').length).toBeGreaterThan(0);
    expect(screen.getByText('Сотрудники подразделения')).toBeInTheDocument();
    expect(screen.getByText('Экономист 1')).toBeInTheDocument();
  });

  it('opens the editor window when a second-level unit block is clicked', () => {
    const viewState = buildViewState();
    useUnitHierarchyPageMock.mockReturnValue(viewState);

    renderView();

    fireEvent.click(screen.getByRole('button', { name: 'Открыть редактор объединения Проект А' }));

    expect(viewState.setSelectedEditorUnitId).toHaveBeenCalledWith(2);
    expect(viewState.setActiveUnitDetailsId).toHaveBeenCalledWith(2);
  });

  it('renders graph editor window and side panel when a second-level unit is opened', () => {
    const viewState = buildViewState();
    viewState.selectedEditorUnitId = 2;
    viewState.editorRootUnit = baseDepartment.children[0]!;
    viewState.activeUnitDetails = baseDepartment.children[0]!;
    viewState.activeUnitParent = baseDepartment;
    viewState.activeUnitPathLabel = 'Финансовый блок / Проект А';
    useUnitHierarchyPageMock.mockReturnValue(viewState);

    renderView();

    expect(screen.getByText(/Граф объединения/)).toBeInTheDocument();
    expect(screen.getAllByText('Проект А').length).toBeGreaterThan(0);
    expect(screen.getByRole('button', { name: 'Добавить дочерний лист' })).toBeInTheDocument();

    const detailsPanel = screen.getByText('Сотрудники объединения').closest('.MuiCard-root');
    expect(detailsPanel).not.toBeNull();
    expect(screen.getByText('Финансовый блок / Проект А')).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: 'Добавить сотрудника' }).length).toBeGreaterThan(0);
  });

  it('shows delete preview dialog when delete state is open', () => {
    const viewState = buildViewState();
    viewState.deleteDialogState = {
      unit: baseDepartment.children[0]!,
      previewTree: [baseDepartment],
      willReassign: true,
    };
    useUnitHierarchyPageMock.mockReturnValue(viewState);

    renderView();

    const dialog = within(screen.getByRole('dialog'));
    expect(dialog.getByText('Удаление объединения')).toBeInTheDocument();
    expect(dialog.getByText('Предпросмотр новой иерархии')).toBeInTheDocument();
    expect(dialog.getAllByText('Проект А').length).toBeGreaterThan(0);
  });
});
