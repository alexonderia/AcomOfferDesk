import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { PageBreadcrumbActionsProvider, usePageBreadcrumbItemsState } from '@app/layouts/PageBreadcrumbActions';
import { BreadcrumbsNav } from '@shared/components/BreadcrumbsNav';
import { getOfferWorkspace } from '@shared/api/offers/getOfferWorkspace';
import { updateOfferStatus } from '@shared/api/offers/updateOfferStatus';
import { createOfferForRequest } from '@shared/api/offers/createOfferForRequest';
import { normalizeChatActions, normalizeOfferActions, normalizeRequestActions } from '@shared/api/mappers';
import type { OfferWorkspace } from '@shared/api/offers/getOfferWorkspace';
import { ROLE } from '@shared/constants/roles';
import { getContractorLoginAccess } from '@shared/api/contractors/getContractorLoginAccess';
import { ContractorLoginAccessBadge } from '@features/contractors/components/ContractorLoginAccessBadge';
import { useOfferWorkspace } from './useOfferWorkspace';
import { ConfirmationDialog } from '@shared/components/ConfirmationDialog';

const mocks = vi.hoisted(() => ({
  session: { login: 'staff', roleId: 4, permissions: [] as string[] },
  client: { subscribe: vi.fn(), unsubscribe: vi.fn() },
  onEvent: vi.fn(),
  loadMessages: vi.fn(),
  setChatActions: vi.fn(),
}));

vi.mock('@app/providers/AuthProvider', () => ({ useAuth: () => ({ session: mocks.session, logout: vi.fn() }) }));
vi.mock('@app/providers/ChatRealtimeProvider', () => ({
  useChatRealtime: () => ({ client: mocks.client, connectionState: 'connected', onEvent: mocks.onEvent }),
}));
vi.mock('@shared/api/offers/getOfferWorkspace', () => ({ getOfferWorkspace: vi.fn() }));
vi.mock('@shared/api/offers/updateOfferStatus', () => ({ updateOfferStatus: vi.fn() }));
vi.mock('@shared/api/offers/createOfferForRequest', () => ({ createOfferForRequest: vi.fn() }));
vi.mock('@shared/api/contractors/getContractorLoginAccess', () => ({ getContractorLoginAccess: vi.fn() }));
vi.mock('@shared/api/offers/getOfferContractorInfo', () => ({
  getOfferContractorInfo: vi.fn().mockRejectedValue(new Error('Contractor details unavailable in fixture')),
}));
vi.mock('./useOfferMessages', () => ({
  useOfferMessages: () => ({
    messages: [], chatActions: {}, setChatActions: mocks.setChatActions,
    isSending: false, chatErrorMessage: null, typingUserIds: [], loadMessages: mocks.loadMessages,
  }),
}));

const workspaceFixture = (canViewDetails = true): OfferWorkspace => {
  const offer = {
    offer_id: 61, status: 'submitted', status_label: 'На рассмотрении',
    created_at: null, updated_at: null, files: [], actions: normalizeOfferActions(),
  };
  return {
    request: {
      request_id: '17', description: null, status: 'open', status_label: 'Открыта',
      deadline_at: '2026-11-17T00:00:00Z', created_at: null, updated_at: null, closed_at: null,
      files: [], actions: normalizeRequestActions({ can_view_details: canViewDetails }),
    },
    offer, offers: [offer], profile: null, company_contacts: null, chatActions: normalizeChatActions(),
  };
};

const Breadcrumbs = () => <BreadcrumbsNav items={usePageBreadcrumbItemsState()} />;
const Workspace = () => {
  const { contractorLoginAccess, isContractorAccessLoading, canDeleteOffer, handleDeleteOffer,
    confirmation, closeConfirmation, isUpdatingOfferStatus, handleStatusChange, handleCreateNewOffer } = useOfferWorkspace();
  return <><Breadcrumbs /><ContractorLoginAccessBadge access={contractorLoginAccess} loading={isContractorAccessLoading} />
    <button type="button" disabled={!canDeleteOffer} onClick={() => void handleDeleteOffer()}>Удалить КП</button>
    <button type="button" onClick={() => void handleStatusChange('accepted')}>Принять КП</button>
    <button type="button" onClick={() => void handleStatusChange('rejected')}>Отклонить КП</button>
    <button type="button" onClick={() => void handleCreateNewOffer()}>Новый отклик</button>
    {confirmation ? <ConfirmationDialog {...confirmation} open isPending={isUpdatingOfferStatus} onCancel={closeConfirmation} /> : null}
  </>;
};
const renderWorkspace = (path = '/offers/61/workspace') => render(
  <MemoryRouter initialEntries={[path]} >
    <PageBreadcrumbActionsProvider>
      <Routes>
        <Route path="/offers/:id/workspace" element={<Workspace />} />
        <Route path="/requests/:id" element={<><Breadcrumbs /><div>Карточка заявки</div></>} />
      </Routes>
    </PageBreadcrumbActionsProvider>
  </MemoryRouter>,
);

describe('offer workspace breadcrumbs', () => {
  it.each(['Принять КП', 'Отклонить КП'])('confirms %s through a dialog before calling the API', async (label) => {
    const workspace = workspaceFixture();
    workspace.offer.actions.accept = true;
    workspace.offer.actions.reject = true;
    vi.mocked(getOfferWorkspace).mockResolvedValue(workspace);
    const status = label === 'Принять КП' ? 'accepted' : 'rejected';
    vi.mocked(updateOfferStatus).mockResolvedValue({ offer: { id: 61, status } });
    renderWorkspace();
    await screen.findByText('КП №61');
    fireEvent.click(screen.getByRole('button', { name: label }));
    const dialog = await screen.findByRole('dialog', { name: 'Изменение статуса КП' });
    expect(updateOfferStatus).not.toHaveBeenCalled();
    fireEvent.click(within(dialog).getByRole('button', { name: 'Отмена' }));
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: label }));
    fireEvent.click(within(await screen.findByRole('dialog')).getByRole('button', { name: 'Подтвердить' }));
    await waitFor(() => expect(updateOfferStatus).toHaveBeenCalledExactlyOnceWith({ offer_id: 61, status }));
  });

  it('confirms creation of a new offer and sends no request when cancelled', async () => {
    const workspace = workspaceFixture();
    workspace.request.actions.create_offer = true;
    vi.mocked(getOfferWorkspace).mockResolvedValue(workspace);
    vi.mocked(createOfferForRequest).mockResolvedValue({ offerId: 61, requestId: '17', workspacePath: '/offers/61/workspace' });
    renderWorkspace();
    await screen.findByText('КП №61');
    fireEvent.click(screen.getByRole('button', { name: 'Новый отклик' }));
    const dialog = await screen.findByRole('dialog', { name: 'Новый отклик' });
    expect(dialog).toHaveTextContent('останутся в истории');
    fireEvent.click(within(dialog).getByRole('button', { name: 'Отмена' }));
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(createOfferForRequest).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Новый отклик' }));
    fireEvent.click(within(await screen.findByRole('dialog')).getByRole('button', { name: 'Создать' }));
    await waitFor(() => expect(createOfferForRequest).toHaveBeenCalledExactlyOnceWith('17'));
  });

  it('keeps deletion open on failure and allows retrying', async () => {
    const workspace = workspaceFixture();
    workspace.offer.actions.delete = true;
    vi.mocked(getOfferWorkspace).mockResolvedValue(workspace);
    vi.mocked(updateOfferStatus).mockRejectedValueOnce(new Error('Не удалось удалить КП'))
      .mockResolvedValueOnce({ offer: { id: 61, status: 'deleted' } });
    renderWorkspace();
    await waitFor(() => expect(screen.getByRole('button', { name: 'Удалить КП' })).toBeEnabled());
    fireEvent.click(screen.getByRole('button', { name: 'Удалить КП' }));
    const dialog = await screen.findByRole('dialog');
    fireEvent.click(within(dialog).getByRole('button', { name: 'Удалить' }));
    await waitFor(() => expect(updateOfferStatus).toHaveBeenCalledOnce());
    await waitFor(() => expect(within(dialog).getByRole('button', { name: 'Удалить' })).toBeEnabled());
    expect(dialog).toBeVisible();
    fireEvent.click(within(dialog).getByRole('button', { name: 'Удалить' }));
    await waitFor(() => expect(updateOfferStatus).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
  });

  afterEach(() => vi.restoreAllMocks());
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.session.roleId = ROLE.PROJECT_MANAGER;
    mocks.session.login = 'staff';
    vi.mocked(getOfferWorkspace).mockResolvedValue(workspaceFixture());
    vi.mocked(getContractorLoginAccess).mockResolvedValue([]);
  });

  it.each([ROLE.SUPERADMIN, ROLE.LEAD_ECONOMIST, ROLE.ECONOMIST])(
    'deletes the selected offer for staff role %s when the server permits it', async (roleId) => {
      mocks.session.roleId = roleId;
      const workspace = workspaceFixture();
      workspace.offer.actions.delete = true;
      const deletedWorkspace = workspaceFixture();
      deletedWorkspace.offer.status = 'deleted';
      vi.mocked(getOfferWorkspace).mockResolvedValueOnce(workspace).mockResolvedValue(deletedWorkspace);
      vi.mocked(updateOfferStatus).mockResolvedValue({ offer: { id: 61, status: 'deleted' } });
      renderWorkspace();
      await waitFor(() => expect(screen.getByRole('button', { name: 'Удалить КП' })).toBeEnabled());
      fireEvent.click(screen.getByRole('button', { name: 'Удалить КП' }));
      const dialog = await screen.findByRole('dialog', { name: 'Удаление КП' });
      expect(updateOfferStatus).not.toHaveBeenCalled();
      fireEvent.click(within(dialog).getByRole('button', { name: 'Удалить' }));
      await waitFor(() => expect(updateOfferStatus).toHaveBeenCalledWith({ offer_id: 61, status: 'deleted' }));
      expect(updateOfferStatus).toHaveBeenCalledOnce();
      await waitFor(() => expect(screen.getByRole('button', { name: 'Удалить КП' })).toBeDisabled());
    },
  );

  it('does not send deletion after cancelling the confirmation', async () => {
    const workspace = workspaceFixture();
    workspace.offer.actions.delete = true;
    vi.mocked(getOfferWorkspace).mockResolvedValue(workspace);
    renderWorkspace();
    await waitFor(() => expect(screen.getByRole('button', { name: 'Удалить КП' })).toBeEnabled());
    fireEvent.click(screen.getByRole('button', { name: 'Удалить КП' }));
    fireEvent.click(within(await screen.findByRole('dialog')).getByRole('button', { name: 'Отмена' }));
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(updateOfferStatus).not.toHaveBeenCalled();
  });

  it.each(['/offers/61/workspace', '/offers/61/workspace?requestId=999'])(
    'uses the loaded request for a notification/direct link %s and clears breadcrumbs on exit', async (path) => {
      renderWorkspace(path);
      const requestLink = await screen.findByRole('button', { name: 'Заявка №17' });
      const breadcrumbs = screen.getByRole('navigation', { name: 'breadcrumb' });
      expect(within(breadcrumbs).getByText('КП №61')).toBeVisible();
      expect(within(breadcrumbs).queryByText('Заявка №999')).not.toBeInTheDocument();
      expect(getOfferWorkspace).toHaveBeenCalledExactlyOnceWith(61);
      fireEvent.click(requestLink);
      expect(await screen.findByText('Карточка заявки')).toBeVisible();
      await waitFor(() => expect(screen.queryByRole('navigation', { name: 'breadcrumb' })).not.toBeInTheDocument());
    },
  );

  it('shows the request number without a navigation action when view_details is denied', async () => {
    vi.mocked(getOfferWorkspace).mockResolvedValue(workspaceFixture(false));
    renderWorkspace();
    expect(await screen.findByText('Заявка №17')).toBeVisible();
    expect(screen.queryByRole('button', { name: 'Заявка №17' })).not.toBeInTheDocument();
  });

  it('keeps the contractor header configuration in charge of its own breadcrumbs', async () => {
    mocks.session.roleId = ROLE.CONTRACTOR;
    renderWorkspace();
    await waitFor(() => expect(mocks.setChatActions).toHaveBeenCalled());
    expect(screen.queryByRole('navigation', { name: 'breadcrumb' })).not.toBeInTheDocument();
  });

  it('checks and displays the signed-in contractor own access', async () => {
    mocks.session.roleId = ROLE.CONTRACTOR;
    mocks.session.login = 'contractor';
    const workspace = workspaceFixture();
    workspace.offer.contractor_user_id = 'contractor';
    workspace.offer.actions.view_contractor_info = true;
    vi.mocked(getOfferWorkspace).mockResolvedValue(workspace);
    vi.mocked(getContractorLoginAccess).mockResolvedValue([{
      user_id: 'contractor', state: 'available', label: 'Вход доступен', description: 'Учётная запись готова ко входу.',
    }]);

    renderWorkspace();

    expect(await screen.findByLabelText('Вход в личный кабинет: Вход доступен')).toBeVisible();
    expect(getContractorLoginAccess).toHaveBeenCalledExactlyOnceWith(['contractor'], expect.any(AbortSignal));
  });

  it('does not check contractor access without the workspace action flag', async () => {
    const workspace = workspaceFixture();
    workspace.offer.contractor_user_id = 'contractor';
    vi.mocked(getOfferWorkspace).mockResolvedValue(workspace);
    renderWorkspace();
    await waitFor(() => expect(mocks.setChatActions).toHaveBeenCalled());
    expect(getContractorLoginAccess).not.toHaveBeenCalled();
  });
});
