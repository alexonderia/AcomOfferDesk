import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { RequestWithOfferStats } from '@shared/api/requests/getRequests';
import { appTheme } from '@shared/theme/appTheme';
import { RequestsTable } from './RequestsTable';

let mobile = false;
vi.mock('@shared/lib/responsive', () => ({
  useIsMobileViewport: () => mobile,
  MOBILE_BOTTOM_NAV_CONTENT_PADDING: 0,
  MOBILE_BOTTOM_NAV_HEIGHT_PX: 0,
  MOBILE_BOTTOM_NAV_OFFSET: 0,
  MOBILE_BOTTOM_NAV_SAFE_AREA: '0px',
}));

const baseRequest = (): RequestWithOfferStats => ({
  id: '101',
  id_user: 'owner-1',
  owner_full_name: 'Owner One',
  status: 'open',
  status_label: 'Open',
  deadline_at: '2026-05-12T00:00:00Z',
  closed_at: null,
  id_offer: null,
  description: 'Sample request',
  created_at: '2026-05-12T00:00:00Z',
  updated_at: '2026-05-12T00:00:00Z',
  files: [],
  actions: {
    view_details: true,
    view_amounts: true,
    open_contractor_view: false,
    edit: false,
    update_status: false,
    change_owner: false,
    upload_file: false,
    delete_file: false,
    send_email_notifications: false,
    mark_deleted_alert_viewed: false,
    create_offer: false,
  },
});

describe('RequestsTable states', () => {
  beforeEach(() => { mobile = false; });

  it.each([false, true])('explains the owner warning next to the responsible employee, mobile=%s', async (isMobile) => {
    mobile = isMobile;
    const warning = 'Заявка не распределена: ответственный сотрудник в чёрном списке.';
    const onRowClick = vi.fn();
    render(<ThemeProvider theme={appTheme}>
      <RequestsTable requests={[{ ...baseRequest(), owner_warning: warning }]} onRowClick={onRowClick} />
    </ThemeProvider>);
    if (isMobile) fireEvent.click(screen.getByRole('button', { name: /Подробнее/ }));
    const icon = await screen.findByRole('img', { name: warning });
    fireEvent.mouseOver(icon);
    expect(await screen.findByRole('tooltip')).toHaveTextContent(warning);
    fireEvent.click(icon);
    expect(onRowClick).not.toHaveBeenCalled();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it.each([false, true])('hides staff warnings from contractors, mobile=%s', (isMobile) => {
    mobile = isMobile;
    const warning = 'Заявка не распределена: ответственный сотрудник неактивен.';
    render(<ThemeProvider theme={appTheme}>
      <RequestsTable requests={[{ ...baseRequest(), owner_warning: warning }]} isContractor />
    </ThemeProvider>);
    if (isMobile) fireEvent.click(screen.getByRole('button', { name: /Подробнее/ }));
    expect(screen.queryByRole('img', { name: warning })).not.toBeInTheDocument();
    expect(screen.queryByText(warning)).not.toBeInTheDocument();
  });
  it('renders empty state when there are no rows', async () => {
    render(
      <ThemeProvider theme={appTheme}>
        <RequestsTable requests={[]} isLoading={false} />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('\u0417\u0430\u044f\u0432\u043a\u0438 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u044b.')).toBeInTheDocument();
    });
  }, 15_000);

  it('renders loading state when table is loading', () => {
    render(
      <ThemeProvider theme={appTheme}>
        <RequestsTable requests={[]} isLoading />
      </ThemeProvider>
    );

    expect(screen.getByText('\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430...')).toBeInTheDocument();
  });

  it('renders data rows when requests are present', () => {
    render(
      <ThemeProvider theme={appTheme}>
        <RequestsTable requests={[baseRequest()]} isLoading={false} />
      </ThemeProvider>
    );

    expect(screen.getByText('Sample request')).toBeInTheDocument();
  });

  it('shows owner selector only for rows with change_owner action', () => {
    const nonEditableOwner = baseRequest();
    const editableOwner: RequestWithOfferStats = {
      ...baseRequest(),
      id: '202',
      id_user: 'owner-2',
      owner_full_name: 'Owner Two',
      actions: {
        ...baseRequest().actions,
        change_owner: true,
      },
    };

    const { rerender } = render(
      <ThemeProvider theme={appTheme}>
        <RequestsTable
          requests={[nonEditableOwner]}
          isLoading={false}
          canEditOwner
          ownerOptionsByRequestId={{
            '202': [
              { id: 'owner-1', label: 'Owner One' },
              { id: 'owner-2', label: 'Owner Two' },
            ],
          }}
        />
      </ThemeProvider>
    );

    const baseComboboxCount = screen.getAllByRole('combobox').length;

    rerender(
      <ThemeProvider theme={appTheme}>
        <RequestsTable
          requests={[nonEditableOwner, editableOwner]}
          isLoading={false}
          canEditOwner
          ownerOptionsByRequestId={{
            '202': [
              { id: 'owner-1', label: 'Owner One' },
              { id: 'owner-2', label: 'Owner Two' },
            ],
          }}
        />
      </ThemeProvider>
    );

    expect(screen.getByText('Owner One')).toBeInTheDocument();
    expect(screen.getByText('Owner Two')).toBeInTheDocument();
    expect(screen.getAllByRole('combobox')).toHaveLength(baseComboboxCount + 1);
  });

  it('shows only latest contractor offer and dropdown for remaining offers', async () => {
    const offerActions = {
      open_workspace: false,
      view_contractor_info: false,
      edit_amount: false,
      accept: false,
      reject: false,
      delete: false,
      upload_file: false,
      delete_file: false,
    };

    const contractorRequest: RequestWithOfferStats = {
      ...baseRequest(),
      id: '202',
      id_user: 'contractor-1',
      owner_full_name: 'Contractor One',
      actions: baseRequest().actions,
      offers: [
        {
          id: 1,
          status: 'accepted',
          unread_messages_count: 0,
          actions: offerActions,
        },
        {
          id: 2,
          status: 'rejected',
          unread_messages_count: 0,
          actions: offerActions,
        },
      ],
    };

    render(
      <ThemeProvider theme={appTheme}>
        <RequestsTable
          requests={[contractorRequest]}
          isLoading={false}
          isContractor
          showContractorOffersColumn
          showContractorNotificationColumn={false}
        />
      </ThemeProvider>
    );

    // Latest offer (highest id) should be visible.
    expect(screen.getByText('КП № 2 Отклонено')).toBeInTheDocument();
    // Dropdown toggle should show remaining count.
    expect(screen.getByText('Ещё: 1')).toBeInTheDocument();

    fireEvent.click(screen.getByTestId('contractor-offers-dropdown-toggle'));

    await waitFor(() => {
      expect(screen.getByText('КП № 1 Принято')).toBeInTheDocument();
    });
  });
});
