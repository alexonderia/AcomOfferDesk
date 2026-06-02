import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ContractorCreateDialog } from './ContractorCreateDialog';

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
