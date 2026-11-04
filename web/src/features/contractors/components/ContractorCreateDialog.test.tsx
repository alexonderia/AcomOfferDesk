import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ContractorCreateDialog } from './ContractorCreateDialog';
import { createManualContractor } from '@shared/api/users/createManualContractor';

vi.mock('@shared/api/users/createManualContractor', () => ({
  createManualContractor: vi.fn()
}));

vi.mock('@shared/ui/toasts', () => ({
  useSystemToasts: () => ({
    showSuccessToast: vi.fn(),
    showErrorToast: vi.fn()
  })
}));

describe('ContractorCreateDialog', () => {
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
