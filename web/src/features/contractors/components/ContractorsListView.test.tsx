import { ThemeProvider } from '@mui/material/styles';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ROLE } from '@shared/constants/roles';
import { appTheme } from '@shared/theme/appTheme';
import type { ContractorListItem } from '@shared/api/contractors/listContractors';
import { ContractorsListView } from './ContractorsListView';

const updateManualContractorMock = vi.fn();
const updateContractorStatusMock = vi.fn();
const getContractorRootUnitsMock = vi.fn();
const updateContractorRootUnitsMock = vi.fn();
const showSystemToastMock = vi.fn();
const showErrorToastMock = vi.fn();

let mockSession: { roleId: number } = {
  roleId: ROLE.ADMIN,
};

vi.mock('@app/providers/AuthProvider', () => ({
  useAuth: () => ({
    session: mockSession,
  }),
}));

vi.mock('@shared/api/users/updateManualContractor', () => ({
  updateManualContractor: (...args: unknown[]) => updateManualContractorMock(...args),
}));

vi.mock('@shared/api/contractors/updateContractorStatus', () => ({
  updateContractorStatus: (...args: unknown[]) => updateContractorStatusMock(...args),
}));

vi.mock('@shared/api/contractors/getContractorRootUnits', () => ({
  getContractorRootUnits: (...args: unknown[]) => getContractorRootUnitsMock(...args),
}));

vi.mock('@shared/api/contractors/updateContractorRootUnits', () => ({
  updateContractorRootUnits: (...args: unknown[]) => updateContractorRootUnitsMock(...args),
}));

vi.mock('@shared/ui/toasts', () => ({
  useSystemToasts: () => ({
    showSystemToast: showSystemToastMock,
    showErrorToast: showErrorToastMock,
  }),
}));

const buildContractor = (): ContractorListItem => ({
  userId: 'contractor-1',
  maxUserId: 'max-42',
  roleId: 3,
  status: 'На проверке',
  fullName: 'Иван Петров',
  phone: '+79990000000',
  mail: 'ivan@example.com',
  companyName: 'ООО Ромашка',
  inn: '1234567890',
  companyPhone: '+79990000001',
  companyMail: 'office@example.com',
  address: 'Москва',
  note: 'Тест',
  createdAt: '2026-06-01T10:00:00Z',
  updatedAt: '2026-06-10T11:00:00Z',
  registrationSource: 'manual',
  actions: {
    view_profile: true,
    update_status: true,
    manage_contractor_unit_bindings: true,
    update_role: false,
    update_manager: false,
    manage_own_profile: false,
    manage_credentials: false,
    manage_company_contacts: false,
    manage_own_unavailability: false,
    manage_subordinate_unavailability: false,
    manage_manual_contractor: true,
  },
  rootUnits: null,
});

const buildContractorsPage = (count: number) => Array.from({ length: count }, (_, index) => ({
  ...buildContractor(),
  userId: `contractor-${index + 1}`,
  fullName: `Контрагент ${index + 1}`,
  companyName: `Компания ${index + 1}`,
}));

const renderView = (props: { contractors?: ReturnType<typeof buildContractor>[] } = {}) => render(
  <ThemeProvider theme={appTheme}>
    <ContractorsListView
      contractors={props.contractors ?? [buildContractor()]}
      emptyMessage="Контрагенты не найдены"
      onStatusUpdated={async () => {}}
    />
  </ThemeProvider>,
);

describe('ContractorsListView editing', () => {
  beforeEach(() => {
    mockSession = {
      roleId: ROLE.ADMIN,
    };
    updateManualContractorMock.mockReset();
    updateContractorStatusMock.mockReset();
    getContractorRootUnitsMock.mockReset();
    updateContractorRootUnitsMock.mockReset();
    showSystemToastMock.mockReset();
    showErrorToastMock.mockReset();

    updateManualContractorMock.mockResolvedValue({ userId: 'contractor-1' });
    updateContractorStatusMock.mockResolvedValue({ userId: 'contractor-1', userStatus: 'active' });
    getContractorRootUnitsMock.mockResolvedValue({
      contractorUserId: 'contractor-1',
      canManage: true,
      items: [
        { unitId: 101, unitName: 'Финансы', isBound: true, canManage: true },
        { unitId: 102, unitName: 'Логистика', isBound: false, canManage: true },
      ],
    });
    updateContractorRootUnitsMock.mockResolvedValue({
      contractorUserId: 'contractor-1',
      canManage: true,
      items: [
        { unitId: 101, unitName: 'Финансы', isBound: true, canManage: true },
        { unitId: 102, unitName: 'Логистика', isBound: true, canManage: true },
      ],
    });
  });

  it('shows read-only cells by default', async () => {
    renderView();

    expect(await screen.findByText('Иван Петров')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Редактировать' })).toBeInTheDocument();
    expect(screen.queryByLabelText('contractor-1-company_name')).not.toBeInTheDocument();
    expect(screen.queryByText('max-42')).not.toBeInTheDocument();
  });

  it('keeps current page while editing a row on another page', async () => {
    renderView({
      contractors: buildContractorsPage(10),
    });

    fireEvent.click(screen.getByRole('button', { name: '2' }));
    expect(screen.getByText('Показаны строки 9-10 из 10')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Редактировать' }));

    const companyInput = await screen.findByLabelText('contractor-9-company_name');
    fireEvent.change(companyInput, { target: { value: 'ООО Обновлено' } });

    expect(screen.getByText('Показаны строки 9-10 из 10')).toBeInTheDocument();
    expect(screen.queryByText('Показаны строки 1-8 из 10')).not.toBeInTheDocument();
  });

  it('saves edited manual contractor fields in edit mode', async () => {
    renderView();

    fireEvent.click(screen.getByRole('button', { name: 'Редактировать' }));

    const companyInput = await screen.findByLabelText('contractor-1-company_name');
    fireEvent.change(companyInput, { target: { value: 'ООО Ландыш' } });
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }));

    await waitFor(() => {
      expect(updateManualContractorMock).toHaveBeenCalledWith('contractor-1', { company_name: 'ООО Ландыш' });
    });
    expect(showSystemToastMock).toHaveBeenCalled();
  });

  it('shows validation error via toast and field icon', async () => {
    renderView();

    fireEvent.click(screen.getByRole('button', { name: 'Редактировать' }));

    const companyMailInput = await screen.findByLabelText('contractor-1-company_mail');
    fireEvent.change(companyMailInput, { target: { value: 'bad-email' } });
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }));

    await waitFor(() => {
      expect(showSystemToastMock).toHaveBeenCalledWith({
        severity: 'warning',
        message: 'contractor-1: Некорректный формат e-mail компании',
      });
    });
    expect(screen.getByLabelText('Некорректный формат e-mail компании')).toBeInTheDocument();
    expect(updateManualContractorMock).not.toHaveBeenCalled();
  });

  it('validates entire row when one cell is edited', async () => {
    renderView({
      contractors: [{
        ...buildContractor(),
        inn: 'yyyyyyyyy',
      }],
    });

    fireEvent.click(screen.getByRole('button', { name: 'Редактировать' }));

    const companyInput = await screen.findByLabelText('contractor-1-company_name');
    fireEvent.change(companyInput, { target: { value: 'Новая компания' } });

    await waitFor(() => {
      expect(screen.getByLabelText('ИНН должен содержать 10 или 12 цифр')).toBeInTheDocument();
    });
  });

  it('does not treat "Не указано" optional values as validation errors', async () => {
    renderView({
      contractors: [{
        ...buildContractor(),
        mail: 'Не указано',
        inn: 'Не указано',
        note: 'Не указано',
      }],
    });

    fireEvent.click(screen.getByRole('button', { name: 'Редактировать' }));

    const companyInput = await screen.findByLabelText('contractor-1-company_name');
    fireEvent.change(companyInput, { target: { value: 'ООО Ландыш' } });

    await waitFor(() => {
      expect(screen.queryByLabelText('ИНН должен содержать 10 или 12 цифр')).not.toBeInTheDocument();
      expect(screen.queryByLabelText('Некорректный формат e-mail контакта')).not.toBeInTheDocument();
    });
  });

  it('keeps login read-only in edit mode', async () => {
    renderView();

    fireEvent.click(screen.getByRole('button', { name: 'Редактировать' }));

    expect(screen.queryByLabelText('contractor-1-login')).not.toBeInTheDocument();
    expect(screen.getAllByLabelText('Поле недоступно для редактирования').length).toBeGreaterThan(0);
  });

  it('hides edit mode when contractor data editing is unavailable', async () => {
    mockSession = {
      roleId: ROLE.PROJECT_MANAGER,
    };

    renderView({
      contractors: [{
        ...buildContractor(),
        actions: {
          ...buildContractor().actions,
          manage_contractor_unit_bindings: true,
          manage_manual_contractor: false,
          update_status: true,
        },
      }],
    });

    expect(await screen.findByText('Иван Петров')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Редактировать' })).not.toBeInTheDocument();
  });

  it('makes the status field editable in edit mode when status access is granted', async () => {
    renderView({
      contractors: [{
        ...buildContractor(),
        actions: {
          ...buildContractor().actions,
          manage_manual_contractor: true,
          update_status: true,
        },
      }],
    });

    fireEvent.click(await screen.findByRole('button', { name: 'Редактировать' }));

    const statusCombobox = await screen.findByRole('combobox', { name: 'contractor-1-status' });
    expect(statusCombobox).toBeInTheDocument();

    fireEvent.mouseDown(statusCombobox);
    fireEvent.click(await screen.findByRole('option', { name: 'Активен' }));

    fireEvent.click(screen.getByRole('button', { name: /Сохранить/ }));

    await waitFor(() => {
      expect(updateContractorStatusMock).toHaveBeenCalledWith('contractor-1', { user_status: 'active' });
    });
  });

  it('locks the status field in edit mode when status access is missing', async () => {
    renderView({
      contractors: [{
        ...buildContractor(),
        actions: {
          ...buildContractor().actions,
          manage_manual_contractor: true,
          update_status: false,
        },
      }],
    });

    fireEvent.click(await screen.findByRole('button', { name: 'Редактировать' }));

    expect(await screen.findByLabelText('contractor-1-full_name')).toBeInTheDocument();
    expect(screen.queryByRole('combobox', { name: 'contractor-1-status' })).not.toBeInTheDocument();
    expect(screen.getAllByLabelText('Поле недоступно для редактирования').length).toBeGreaterThan(0);
  });

  it('allows status update from contractor details dialog', async () => {
    mockSession = {
      roleId: ROLE.PROJECT_MANAGER,
    };

    renderView({
      contractors: [{
        ...buildContractor(),
        actions: {
          ...buildContractor().actions,
          manage_contractor_unit_bindings: true,
          manage_manual_contractor: false,
          update_status: true,
        },
      }],
    });

    fireEvent.click(await screen.findByText('Иван Петров'));

    expect(await screen.findByText('Изменение статуса')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Сохранить статус' })).toBeInTheDocument();
  });

  it('shows lock icons on always read-only fields in edit mode', async () => {
    renderView();

    fireEvent.click(screen.getByRole('button', { name: 'Редактировать' }));

    await screen.findByText('max-42');
    expect(screen.getAllByLabelText('Поле недоступно для редактирования').length).toBeGreaterThanOrEqual(3);
  });

  it('binds contractor root units directly from the table column', async () => {
    renderView();

    fireEvent.click(await screen.findByLabelText('root-units-contractor-1'));

    expect(await screen.findByLabelText('Финансы')).toBeChecked();
    const logisticsCheckbox = await screen.findByLabelText('Логистика');
    expect(logisticsCheckbox).not.toBeChecked();

    fireEvent.click(logisticsCheckbox);
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить' }));

    await waitFor(() => {
      expect(updateContractorRootUnitsMock).toHaveBeenCalledWith('contractor-1', [101, 102]);
    });
    expect(showSystemToastMock).toHaveBeenCalledWith({
      severity: 'success',
      message: 'Привязки к подразделениям сохранены.',
    });
    expect(screen.queryByText('Карточка контрагента')).not.toBeInTheDocument();
    expect(updateContractorStatusMock).not.toHaveBeenCalled();
  });

  it('uses preloaded bindings from the list without an extra fetch', async () => {
    renderView({
      contractors: [{
        ...buildContractor(),
        rootUnits: {
          contractorUserId: 'contractor-1',
          canManage: true,
          items: [
            { unitId: 101, unitName: 'Финансы', isBound: true, canManage: true },
            { unitId: 102, unitName: 'Логистика', isBound: false, canManage: true },
          ],
        },
      }],
    });

    expect(await screen.findByLabelText('root-units-contractor-1')).toHaveTextContent('Привязок: 1');

    fireEvent.click(screen.getByLabelText('root-units-contractor-1'));

    expect(await screen.findByLabelText('Финансы')).toBeChecked();
    expect(getContractorRootUnitsMock).not.toHaveBeenCalled();
  });

  it('loads and saves contractor root unit bindings', async () => {
    renderView();

    fireEvent.click(await screen.findByText('Иван Петров'));

    expect(await screen.findByLabelText('Финансы')).toBeChecked();
    const logisticsCheckbox = await screen.findByLabelText('Логистика');
    expect(logisticsCheckbox).not.toBeChecked();

    fireEvent.click(logisticsCheckbox);
    fireEvent.click(screen.getByRole('button', { name: 'Сохранить привязки' }));

    await waitFor(() => {
      expect(updateContractorRootUnitsMock).toHaveBeenCalledWith('contractor-1', [101, 102]);
    });
    expect(showSystemToastMock).toHaveBeenCalledWith({
      severity: 'success',
      message: 'Привязки к подразделениям сохранены.',
    });
  });
});
