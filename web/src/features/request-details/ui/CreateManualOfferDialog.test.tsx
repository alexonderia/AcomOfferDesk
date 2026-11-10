import { ThemeProvider } from '@mui/material/styles';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createManualOfferForRequest } from '@shared/api/offers/createManualOfferForRequest';
import { getRequestContractors, type RequestContractorItem } from '@shared/api/users/getRequestContractors';
import { appTheme } from '@shared/theme/appTheme';
import { CreateManualOfferDialog } from './CreateManualOfferDialog';
import { getManualContractorDuplicates, type ManualContractorDuplicate } from '@shared/api/users/getManualContractorDuplicates';

vi.mock('@shared/api/users/getRequestContractors', () => ({ getRequestContractors: vi.fn() }));
vi.mock('@shared/api/offers/createManualOfferForRequest', () => ({ createManualOfferForRequest: vi.fn() }));
vi.mock('@shared/api/users/getManualContractorDuplicates', () => ({ getManualContractorDuplicates: vi.fn() }));
vi.mock('@shared/ui/toasts', () => ({ useToastMessageEffect: vi.fn() }));

const reason = 'Данный контрагент уже приложил КП к текущей заявке';
const duplicate = (canSelect = true): ManualContractorDuplicate => ({
  userId: 'existing', companyName: 'ООО Бетон', inn: '7707083893',
  fullName: null, phone: null, mail: null, companyPhone: '+79991234567',
  companyMail: null, address: null, note: null, status: 'active',
  createdAt: null, updatedAt: null, canSelect, disabledReason: canSelect ? null : reason,
});
const contractor = (canSelect: boolean): RequestContractorItem => ({
  user_id: canSelect ? 'available' : 'existing',
  full_name: null,
  company_name: canSelect ? 'ООО Новый' : 'ООО Бетон',
  mail: null,
  company_mail: null,
  can_select: canSelect,
  disabled_reason: canSelect ? null : reason,
});

const renderDialog = () => {
  const onCreated = vi.fn();
  render(
    <ThemeProvider theme={appTheme}>
      <CreateManualOfferDialog open requestId="request-1" onClose={vi.fn()} onCreated={onCreated} />
    </ThemeProvider>
  );
  return { onCreated };
};

const openContractors = async () => {
  await waitFor(() => expect(getRequestContractors).toHaveBeenCalledWith('request-1'));
  fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Выберите контрагента' }));
  return screen.findAllByRole('option');
};

describe('CreateManualOfferDialog contractor selection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getManualContractorDuplicates).mockResolvedValue([]);
    vi.mocked(createManualOfferForRequest).mockResolvedValue({
      offerId: 61, requestId: 'request-1', contractorUserId: 'available',
      contractorCreated: false, workspacePath: '/offers/61',
    });
  });

  const switchToNew = () => {
    fireEvent.mouseDown(screen.getAllByRole('combobox')[0]);
    fireEvent.click(screen.getByRole('option', { name: 'Создать нового' }));
  };

  it('searches duplicates for the current request and reuses the selected contractor while keeping amount and files', async () => {
    vi.mocked(getRequestContractors).mockResolvedValue({ items: [] });
    vi.mocked(getManualContractorDuplicates).mockResolvedValue([duplicate()]);
    renderDialog();
    switchToNew();
    fireEvent.change(screen.getByLabelText('Наименование компании'), { target: { value: 'Бетон' } });
    fireEvent.change(screen.getByLabelText('Сумма КП, руб. (необязательно)'), { target: { value: '123,45' } });
    const file = new File(['offer'], 'КП.txt', { type: 'text/plain' });
    fireEvent.change(document.querySelector('input[type="file"]')!, { target: { files: [file] } });

    fireEvent.click(await screen.findByRole('button', { name: 'Использовать этого контрагента' }));
    expect(getManualContractorDuplicates).toHaveBeenCalledWith({
      requestId: 'request-1', companyName: 'Бетон', inn: '', companyMail: '',
    });
    expect(screen.getByRole('combobox', { name: 'Выберите контрагента' })).toHaveValue('ООО Бетон (existing)');
    fireEvent.click(screen.getByRole('button', { name: 'Создать КП' }));
    await waitFor(() => expect(createManualOfferForRequest).toHaveBeenCalledWith('request-1', {
      contractor_mode: 'existing', contractor_user_id: 'existing', offer_amount: 123.45, files: [file],
    }));
  });

  it('shows an existing offer duplicate without allowing it to be reused', async () => {
    vi.mocked(getRequestContractors).mockResolvedValue({ items: [contractor(false)] });
    vi.mocked(getManualContractorDuplicates).mockResolvedValue([duplicate(false)]);
    renderDialog();
    switchToNew();
    fireEvent.change(screen.getByLabelText('ИНН'), { target: { value: '7707083893' } });

    expect(await screen.findByRole('button', { name: 'Использовать этого контрагента' })).toBeDisabled();
    expect(screen.getByText(reason)).toBeVisible();
    expect(screen.getByLabelText('ИНН')).toHaveValue('7707083893');
    expect(createManualOfferForRequest).not.toHaveBeenCalled();
  });

  it('shows an existing offer contractor as disabled with a hover tooltip and no empty-list notice', async () => {
    vi.mocked(getRequestContractors).mockResolvedValue({ items: [contractor(false)] });
    renderDialog();
    const [option] = await openContractors();

    expect(option).toHaveAttribute('aria-disabled', 'true');
    expect(option).toHaveTextContent(reason);
    expect(screen.queryByText(/Нет доступных контрагентов/)).not.toBeInTheDocument();
    fireEvent.mouseOver(option);
    expect(await screen.findByRole('tooltip')).toHaveTextContent(reason);
    fireEvent.click(option);
    expect(screen.getByRole('combobox', { name: 'Выберите контрагента' })).toHaveValue('');
    expect(screen.getByRole('listbox')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Создать КП' })).toBeDisabled();
    expect(createManualOfferForRequest).not.toHaveBeenCalled();
  });

  it('blocks the disabled option by keyboard and allows selecting and submitting another contractor', async () => {
    vi.mocked(getRequestContractors).mockResolvedValue({ items: [contractor(false), contractor(true)] });
    const { onCreated } = renderDialog();
    await openContractors();
    const input = screen.getByRole('combobox', { name: 'Выберите контрагента' });

    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(input).toHaveValue('');
    expect(screen.getByRole('button', { name: 'Создать КП' })).toBeDisabled();

    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(input).toHaveValue('ООО Новый (available)');
    fireEvent.click(screen.getByRole('button', { name: 'Создать КП' }));
    await waitFor(() => expect(onCreated).toHaveBeenCalledWith('/offers/61'));
    expect(createManualOfferForRequest).toHaveBeenCalledWith('request-1', {
      contractor_mode: 'existing', contractor_user_id: 'available', offer_amount: null, files: [],
    });
  });
});
