import { ThemeProvider } from '@mui/material/styles';
import { fireEvent, render, screen, within } from '@testing-library/react';
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
      members: [
        {
          user_id: 'lead-77',
          full_name: 'Шамина Анжелина Алексеевна',
          role_id: 5,
          role_name: 'Ведущий экономист',
          status: 'active',
        },
      ],
      children: [
        {
          unit_id: 12,
          name: 'Модуль 2',
          id_parent: 11,
          is_active: true,
          members: [
            {
              user_id: 'econ-11',
              full_name: 'Щербакова Виктория Валерьевна',
              role_id: 6,
              role_name: 'Экономист',
              status: 'active',
            },
          ],
          children: [],
          actions: {
            canCreateChild: true,
            canUpdate: true,
            canDeactivate: true,
            canManageMembers: true,
          },
        },
      ],
      actions: {
        canCreateChild: true,
        canUpdate: true,
        canDeactivate: true,
        canManageMembers: true,
      },
    },
    {
      unit_id: 21,
      name: 'Административный блок',
      id_parent: null,
      is_active: true,
      members: [],
      children: [
        {
          unit_id: 22,
          name: 'Модуль А',
          id_parent: 21,
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
  unitOptions: [
    { unitId: 11, label: 'Финансовый блок' },
    { unitId: 12, label: 'Финансовый блок / Модуль 2' },
    { unitId: 21, label: 'Административный блок' },
    { unitId: 22, label: 'Административный блок / Модуль А' },
  ],
  memberUnitByUserId: {
    'chief-1': [
      {
        unitId: 11,
        unitName: 'Финансовый блок',
        label: 'Финансовый блок',
        depth: 0,
      },
    ],
    'lead-1': [
      {
        unitId: 11,
        unitName: 'Финансовый блок',
        label: 'Финансовый блок',
        depth: 0,
      },
      {
        unitId: 12,
        unitName: 'Модуль 2',
        label: 'Финансовый блок / Модуль 2',
        depth: 1,
      },
      {
        unitId: 21,
        unitName: 'Административный блок',
        label: 'Административный блок',
        depth: 0,
      },
      {
        unitId: 22,
        unitName: 'Модуль А',
        label: 'Административный блок / Модуль А',
        depth: 1,
      },
    ],
  },
  unassignedRecommendedMembers: [
    {
      user_id: 'chief-1',
      full_name: 'Ахметшин Ренат Габдельфатович',
      role_id: 1,
      role_name: 'Главный специалист',
      status: 'active',
      parentDisplayName: null,
    },
  ],
  unitDialogMode: null,
  activeUnit: null,
  unitName: '',
  setUnitName: vi.fn(),
  isSavingUnit: false,
  createAssigneeSearch: '',
  setCreateAssigneeSearch: vi.fn(),
  createAvailableUsers: [],
  selectedCreateUserId: '',
  setSelectedCreateUserId: vi.fn(),
  isLoadingCreateUsers: false,
  isMemberDialogOpen: false,
  availableUsers: [],
  selectedUserId: '',
  setSelectedUserId: vi.fn(),
  memberSearch: '',
  setMemberSearch: vi.fn(),
  isLoadingUsers: false,
  isSavingMember: false,
  isAssigningRecommendedUserId: null,
  isDetachingRecommendedAssignmentKey: null,
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
  assignRecommendedMemberToUnit: vi.fn(),
  detachRecommendedMemberFromUnit: vi.fn(),
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

  it('renders the combined hierarchy in a single window with a department filter', () => {
    renderView();

    expect(screen.getByText('Объединенная иерархия')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Объединенная схема' })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getAllByText('Финансовый блок').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Рахматуллин Асхат Ирекович').length).toBeGreaterThan(1);
    expect(screen.getByLabelText('Подразделения')).toBeInTheDocument();
  });

  it('can switch the units hierarchy into all participants mode and open the unit details side panel', () => {
    renderView();

    fireEvent.click(screen.getByRole('button', { name: 'Иерархия юнитов' }));

    expect(screen.getByRole('heading', { name: 'Иерархия юнитов' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Структура' })).toHaveAttribute('aria-pressed', 'true');

    fireEvent.click(screen.getByRole('button', { name: 'Все участники' }));

    expect(screen.getByRole('button', { name: 'Все участники' })).toHaveAttribute('aria-pressed', 'true');

    fireEvent.click(screen.getByRole('button', { name: 'Открыть состав юнита Финансовый блок' }));

    const panel = within(screen.getByRole('complementary', { name: 'Состав юнита' }));
    expect(panel.getByText('Состав юнита')).toBeInTheDocument();
    expect(panel.getByText('Шамина Анжелина Алексеевна')).toBeInTheDocument();
    expect(panel.getByRole('button', { name: 'Добавить сотрудника' })).toBeInTheDocument();
    expect(panel.getByRole('button', { name: 'Удалить участника Шамина Анжелина Алексеевна' })).toBeInTheDocument();
    expect(screen.queryByRole('dialog', { name: 'Состав юнита' })).not.toBeInTheDocument();
  });

  it('shows empty participant state inside the unit details side panel', () => {
    renderView();

    fireEvent.click(screen.getByRole('button', { name: 'Иерархия юнитов' }));
    fireEvent.click(screen.getByRole('button', { name: 'Все участники' }));
    fireEvent.click(screen.getByRole('button', { name: 'Открыть состав юнита Административный блок' }));

    const panel = within(screen.getByRole('complementary', { name: 'Состав юнита' }));
    expect(panel.getByText('В этом юните пока нет участников.')).toBeInTheDocument();
    expect(panel.getByRole('button', { name: 'Добавить сотрудника' })).toBeInTheDocument();
    expect(screen.getAllByText('Место для нового юнита').length).toBeGreaterThan(0);
  });

  it('shows manager info and all current assignments inside the employee dialog', () => {
    renderView();

    fireEvent.click(screen.getByRole('button', { name: 'Изменить привязки Рахматуллин Асхат Ирекович / Модуль 2' }));
    const dialog = within(screen.getByRole('dialog'));

    expect(dialog.getByText('Руководитель сотрудника')).toBeInTheDocument();
    expect(dialog.getByText('Ахметшин Ренат Габдельфатович')).toBeInTheDocument();
    expect(dialog.getByText('Главный специалист')).toBeInTheDocument();
    expect(dialog.getAllByText('Финансовый блок / Модуль 2').length).toBeGreaterThan(0);
    expect(dialog.getByText('Административный блок / Модуль А')).toBeInTheDocument();
    expect(dialog.getByRole('button', { name: 'Открепить от Модуль 2' })).toBeInTheDocument();
    expect(dialog.getByRole('button', { name: 'Открепить от Модуль А' })).toBeInTheDocument();
  });

  it('duplicates an employee for each assignment on the combined hierarchy', () => {
    renderView();

    expect(screen.getAllByText('Рахматуллин Асхат Ирекович')).toHaveLength(4);
    expect(screen.getAllByText('Ведущий специалист')).toHaveLength(4);
    expect(screen.getByText('Финансовый блок / Модуль 2')).toBeInTheDocument();
    expect(screen.getByText('Административный блок / Модуль А')).toBeInTheDocument();
  });

  it('keeps a hierarchy member without a unit inside the manager chain', () => {
    const viewState = buildViewState();
    const unitlessNode = {
      user_id: 'economist-2',
      full_name: 'Сидоров Алексей',
      role_id: 6,
      role_name: 'Экономист',
      status: 'active',
      id_parent_user: 'lead-1',
      children: [],
    };
    viewState.memberUnitByUserId = {
      'chief-1': [
        {
          unitId: 11,
          unitName: 'Финансовый блок',
          label: 'Финансовый блок',
          depth: 0,
        },
      ],
      'lead-1': [
        {
          unitId: 11,
          unitName: 'Финансовый блок',
          label: 'Финансовый блок',
          depth: 0,
        },
      ],
    };
    viewState.recommendedTree = [
      {
        ...viewState.recommendedTree[0]!,
        children: [
          {
            ...viewState.recommendedTree[0]!.children[0]!,
            children: [unitlessNode] as unknown as typeof viewState.recommendedTree[0]['children'][0]['children'],
          },
        ],
      },
    ] as typeof viewState.recommendedTree;
    useUnitHierarchyPageMock.mockReturnValue(viewState);

    renderView();

    expect(screen.getByText('Сидоров Алексей')).toBeInTheDocument();
    expect(screen.getAllByText('Без юнита')).toHaveLength(1);
  });
});
