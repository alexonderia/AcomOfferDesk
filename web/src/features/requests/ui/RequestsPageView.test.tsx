import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { RequestsPageView } from './RequestsPageView';

const useRequestsPageMock = vi.fn();
const showErrorToastMock = vi.fn();
const showSuccessToastMock = vi.fn();

vi.mock('@features/requests/model/useRequestsPage', () => ({
  useRequestsPage: () => useRequestsPageMock(),
}));

vi.mock('@features/requests/ui/RequestsTable', () => ({
  RequestsTable: () => <div data-testid="requests-table-mock" />,
}));

vi.mock('@shared/ui/toasts', () => ({
  useSystemToasts: () => ({
    showErrorToast: showErrorToastMock,
    showSuccessToast: showSuccessToastMock,
  }),
}));

describe('RequestsPageView', () => {
  it('shows error toast from requests hook errorMessage', () => {
    showErrorToastMock.mockReset();
    showSuccessToastMock.mockReset();
    useRequestsPageMock.mockReturnValue({
      canCreateRequest: false,
      canEditOwner: false,
      chatAlertsMap: {},
      errorMessage: 'Request loading failed',
      handleOwnerChange: vi.fn(),
      isContractor: false,
      isLoading: false,
      ownerOptions: [],
      requests: [],
      successToastEvent: null,
      shouldLoadOpenRequests: false,
    });

    render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <RequestsPageView />
      </MemoryRouter>
    );

    expect(screen.getByTestId('requests-table-mock')).toBeInTheDocument();
    expect(showErrorToastMock).toHaveBeenCalledWith('Request loading failed');
  });

  it('shows success toast from requests hook successToastEvent', () => {
    showErrorToastMock.mockReset();
    showSuccessToastMock.mockReset();
    useRequestsPageMock.mockReturnValue({
      canCreateRequest: false,
      canEditOwner: false,
      chatAlertsMap: {},
      errorMessage: null,
      handleOwnerChange: vi.fn(),
      isContractor: false,
      isLoading: false,
      ownerOptions: [],
      requests: [],
      successToastEvent: {
        id: 1,
        message: 'Ответственный по заявке изменен',
      },
      shouldLoadOpenRequests: false,
    });

    render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <RequestsPageView />
      </MemoryRouter>
    );

    expect(screen.getByTestId('requests-table-mock')).toBeInTheDocument();
    expect(showSuccessToastMock).toHaveBeenCalledWith('Ответственный по заявке изменен');
  });
});
