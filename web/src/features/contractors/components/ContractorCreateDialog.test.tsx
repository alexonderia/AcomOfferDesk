import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ContractorCreateDialog } from './ContractorCreateDialog';
import { createManualContractor } from '@shared/api/users/createManualContractor';
import { getManualContractorDuplicates } from '@shared/api/users/getManualContractorDuplicates';

vi.mock('@shared/api/users/createManualContractor', () => ({
  createManualContractor: vi.fn()
}));

vi.mock('@shared/api/users/getManualContractorDuplicates', () => ({
  getManualContractorDuplicates: vi.fn().mockResolvedValue([]),
}));

vi.mock('@shared/ui/toasts', () => ({
  useSystemToasts: () => ({
    showSuccessToast: vi.fn(),
    showErrorToast: vi.fn()
  })
}));

describe('ContractorCreateDialog', () => {
  it('updates filled labels after duplicate selection and clears optional placeholders', async () => {
    vi.mocked(getManualContractorDuplicates).mockResolvedValue([{
      userId: 'beton', companyName: 'ООО Бетон', inn: '7707083893',
      companyPhone: '+79991234567', companyMail: 'Не указано', address: 'Не указано', note: 'Не указано',
      fullName: null, phone: null, mail: null, status: 'active',
      createdAt: '2026-11-10 10:55:14.908719', updatedAt: '2026-11-10 11:07:59.123456',
    }]);
    render(<ContractorCreateDialog open onClose={vi.fn()} onCreated={vi.fn()} />);
    fireEvent.change(document.querySelector('input[name="companyName"]')!, { target: { value: 'Бетон' } });
    expect(await screen.findByText(/10\.11\.2026,\s+10:55/)).toBeVisible();
    expect(screen.getByText(/10\.11\.2026,\s+11:07/)).toBeVisible();
    expect(screen.queryByText(/14\.908719|59\.123456/)).not.toBeInTheDocument();
    fireEvent.click(await screen.findByRole('button', { name: 'Использовать этого контрагента' }));

    const inn = document.querySelector('input[name="inn"]')!;
    expect(inn).toHaveValue('7707083893');
    expect(inn.closest('.MuiFormControl-root')?.querySelector('label')).toHaveAttribute('data-shrink', 'true');
    for (const field of ['companyMail', 'address', 'note']) {
      expect(document.querySelector(`[name="${field}"]`)).toHaveValue('');
    }
    // Filled labels must remain lifted after the user changes and leaves INN.
    fireEvent.change(inn, { target: { value: '123456789012' } });
    fireEvent.blur(inn);
    expect(inn).toHaveValue('123456789012');
    expect(inn.closest('.MuiFormControl-root')?.querySelector('label')).toHaveAttribute('data-shrink', 'true');
    vi.mocked(getManualContractorDuplicates).mockResolvedValue([]);
  });

  it('creates portal access without email when mail is disabled', async () => {
    vi.mocked(createManualContractor).mockResolvedValue({ userId: 'contractor-access', outcome: 'created', duplicate: null });
    const onCreated = vi.fn().mockResolvedValue(undefined);
    render(<ContractorCreateDialog open emailEnabled={false} onClose={vi.fn()} onCreated={onCreated} />);
    fireEvent.change(document.querySelector('input[name="companyName"]') as HTMLInputElement, { target: { value: 'New company' } });
    fireEvent.change(document.querySelector('input[name="inn"]') as HTMLInputElement, { target: { value: '7707083893' } });
    fireEvent.change(document.querySelector('input[name="companyPhone"]') as HTMLInputElement, { target: { value: '+79991234567' } });
    fireEvent.change(screen.getByLabelText('Логин для входа', { exact: false }), { target: { value: 'contractor-access' } });
    fireEvent.change(screen.getByLabelText(/^Начальный пароль\s*\*?$/), { target: { value: 'Initial password 123' } });
    fireEvent.change(screen.getByLabelText(/^Повтор начального пароля\s*\*?$/), { target: { value: 'Initial password 123' } });
    fireEvent.click(screen.getByRole('button', { name: 'Добавить контрагента' }));
    await waitFor(() => expect(onCreated).toHaveBeenCalledOnce());
    expect(createManualContractor).toHaveBeenCalledWith(expect.objectContaining({ login: 'contractor-access', password: 'Initial password 123', password_confirmation: 'Initial password 123', company_mail: undefined }));
  }, 15000);

  it('shows required markers for mandatory fields and updates them live when values become valid', () => {
    render(
      <ContractorCreateDialog
        open
        onClose={() => undefined}
        onCreated={async () => undefined}
      />
    );

    expect(screen.getAllByTitle('Обязательное поле').length).toBeGreaterThanOrEqual(3);

    fireEvent.change(document.querySelector('input[name="companyName"]') as HTMLInputElement, {
      target: { value: 'ООО Ромашка' }
    });
    fireEvent.change(document.querySelector('input[name="inn"]') as HTMLInputElement, {
      target: { value: '1234567890' }
    });
    fireEvent.change(document.querySelector('input[name="companyPhone"]') as HTMLInputElement, {
      target: { value: '+7 900 123-45-67' }
    });

    expect(screen.getAllByTitle('Поле заполнено верно').length).toBeGreaterThanOrEqual(3);
  });
});
