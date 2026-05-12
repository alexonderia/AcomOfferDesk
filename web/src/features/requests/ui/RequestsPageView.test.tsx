import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { RequestsPageView } from './RequestsPageView';

const useRequestsPageMock = vi.fn();

vi.mock('@features/requests/model/useRequestsPage', () => ({
  useRequestsPage: () => useRequestsPageMock(),
}));

vi.mock('@features/requests/ui/RequestsTable', () => ({
  RequestsTable: () => <div data-testid="requests-table-mock" />,
}));

describe('RequestsPageView', () => {
  it('renders error state message from requests hook', () => {
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
      shouldLoadOpenRequests: false,
    });

    render(
      <MemoryRouter>
        <RequestsPageView />
      </MemoryRouter>
    );

    expect(screen.getByText('Request loading failed')).toBeInTheDocument();
  });
});
