import { fireEvent, render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { appTheme } from '@shared/theme/appTheme';
import type { RequestDetailsOffer } from '@shared/api/requests/getRequestDetails';
import { OffersTable } from './OffersTable';

let mobile = false;
vi.mock('@shared/lib/responsive', () => ({ useIsMobileViewport: () => mobile }));
const offer = {
  offer_id: 60, contractor_user_id: 'one', status: 'submitted', contractor_company_name: 'ООО Бетон',
  created_at: '2026-11-10T10:00:00', updated_at: '2026-11-10T10:00:00', files: [],
  actions: { view_contractor_info: true },
} as unknown as RequestDetailsOffer;
const renderTable = (allowed = true) => render(<ThemeProvider theme={appTheme}>
  <OffersTable offers={[{ ...offer, actions: { ...offer.actions, view_contractor_info: allowed } }]}
    statusMap={{}} statusOptions={[]} onStatusChange={vi.fn()} onOpenWorkspace={vi.fn()} onDownloadFile={vi.fn()}
    contractorLoginAccess={new Map([['one', { user_id: 'one', state: 'password_not_set', label: 'Пароль не задан', description: 'Установите пароль для входа.' }]])} />
</ThemeProvider>);

describe('OffersTable contractor access', () => {
  beforeEach(() => { mobile = false; });
  it.each([false, true])('shows login status in contractor data, mobile=%s', (isMobile) => {
    mobile = isMobile;
    renderTable();
    if (isMobile) fireEvent.click(screen.getByRole('button', { name: /Подробнее/ }));
    expect(screen.getByLabelText('Вход в личный кабинет: Пароль не задан')).toBeVisible();
  });
  it('does not expose login metadata without the backend action', () => {
    renderTable(false);
    expect(screen.queryByLabelText('Вход в личный кабинет: Пароль не задан')).not.toBeInTheDocument();
  });
});
