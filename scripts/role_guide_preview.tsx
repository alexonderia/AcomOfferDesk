// Documentation-only preview. Never imported by the application entrypoint.
import React from 'react';
import { createRoot } from 'react-dom/client';
import { Box, CssBaseline, Stack, ThemeProvider, Typography } from '@mui/material';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { SnackbarProvider } from 'notistack';
import { useForm } from 'react-hook-form';
import { AuthProvider, useAuth } from '@app/providers/AuthProvider';
import { ChatRealtimeProvider } from '@app/providers/ChatRealtimeProvider';
import { PageBreadcrumbActionsProvider } from '@app/layouts/PageBreadcrumbActions';
import { ContractorRequestDetailsPage } from '@pages/requests/ContractorRequestDetailsPage';
import { CreateRequestPage } from '@pages/requests/CreateRequestPage';
import { SystemStatusPage } from '@pages/system-status/SystemStatusPage';
import { RequestDetailsView } from '@features/request-details/ui/RequestDetailsView';
import { CreateManualOfferDialog } from '@features/request-details/ui/CreateManualOfferDialog';
import { OfferWorkspaceView } from '@features/offer-workspace/ui/OfferWorkspaceView';
import { OfferWorkspaceChatPanel } from '@features/requests/ui/OfferWorkspaceChatPanel';
import { NotificationCenterPanel } from '@features/notifications/ui/NotificationCenterPanel';
import { NormativeFilesPageView } from '@features/normative-files/ui/NormativeFilesPageView';
import { ContractorInviteDialog } from '@features/contractors/components/ContractorInviteDialog';
import { ContractorsListView } from '@features/contractors/components/ContractorsListView';
import { EmployeeCardDialog } from '@features/admin/components/EmployeeCardDialog';
import { UsersTable } from '@features/admin/components/UsersTable';
import { PlanKpiRow } from '@features/dashboard/components/plan/PlanOverviewSections';
import { PlanDialogs } from '@features/dashboard/components/plan/PlanDialogs';
import type { RootPlanFormValues, SubplanFormValues, DelegateFormValues, EditFormValues } from '@features/dashboard/components/plan/planDashboardForms';
import { CircularProcessChart } from '@features/dashboard/components/DashboardCharts';
import { FeedbackButton } from '@shared/components/FeedbackButton';
import { FilePreviewDialog } from '@shared/components/file-preview/FilePreviewDialog';
import { PasswordChangeForm } from '@shared/components/PasswordChangeForm';
import { UserPasswordResetButton } from '@shared/components/UserPasswordResetButton';
import { appTheme } from '@shared/theme/appTheme';
import '@shared/theme/typography.css';
import { UnitOrgChart } from '@features/unit-hierarchy/ui/UnitOrgChart';
import { RequestsTable } from '@features/requests/ui/RequestsTable';
import { RoleGuideDialog } from '@shared/components/RoleGuideButton';
import { roleGuides } from '@shared/content/roleGuides';
import type { UnitNode, UnitMember } from '@shared/api/units';
import type { RequestWithOfferStats } from '@shared/api/requests/getRequests';
import type { ContractorListItem } from '@shared/api/contractors/listContractors';
import { normalizeOfferActions, normalizeRequestActions, normalizeUserActions } from '@shared/api/mappers';
import { ROLE } from '@shared/constants/roles';

const person = (id: string, full_name: string, role_id: number, role_name: string): UnitMember => ({
  user_id: id, full_name, role_id, role_name, status: 'active', id_parent_user: null,
});
const unit = (unit_id: number, name: string, id_parent: number | null, members: UnitMember[], children: UnitNode[] = []): UnitNode => ({
  unit_id, name, id_parent, is_active: true, members, children,
  actions: { canCreateChild: false, canUpdate: false, canDelete: false, canManageMembers: false },
});
const tree = [unit(1, 'Учебное подразделение', null, [person('rp', 'Роман', 4, 'Руководитель проекта')], [
  unit(2, 'Объединение А', 1, [person('ve', 'Анна', 5, 'Ведущий экономист'), person('e1', 'Борис', 6, 'Экономист')], [
    unit(4, 'Вложенная группа', 2, [person('e2', 'Вера', 6, 'Экономист')]),
  ]),
  unit(3, 'Объединение Б', 1, [person('other', 'Другая команда', 5, 'Ведущий экономист')]),
])];

const params = new URLSearchParams(location.search);
const view = params.get('view') ?? 'hierarchy';
const contractor = ['requests-contractor', 'contractor-available', 'contractor-respond', 'contractor-edit',
  'contractor-files', 'contractor-chat', 'contractor-notifications'].includes(view);
const noop = () => undefined;
const asyncNoop = async () => undefined;
const trainingDate = '2026-11-19T09:00:00Z';
const documentName = 'Учебная спецификация.png';
const request = (id: string, status: string, description: string, ownStatus: string): RequestWithOfferStats => ({
  id, id_user: 'example-owner', owner_full_name: 'Контакт по заявке', status,
  status_label: status === 'closed' ? 'закрыта' : 'открыта',
  deadline_at: '2026-11-30T12:00:00Z', created_at: '2026-11-19T09:00:00Z', updated_at: '2026-11-19T09:00:00Z',
  closed_at: status === 'closed' ? '2026-11-19T09:00:00Z' : null,
  id_offer: status === 'closed' ? 2 : null, description, files: [],
  count_submitted: status === 'closed' ? 0 : 2, count_accepted_total: status === 'closed' ? 1 : 0, count_rejected_total: 0,
  unread_messages_count: id === 'УЧ-001' ? 2 : 0,
  actions: normalizeRequestActions({ can_view_details: true, can_open_contractor_view: contractor, can_view_amounts: !contractor }),
  offers: contractor ? [{ id: id === 'УЧ-001' ? 1 : 2, status: ownStatus, unread_messages_count: id === 'УЧ-001' ? 2 : 0,
    actions: normalizeOfferActions({ can_open_workspace: true }) }] : [],
});
const requests = [
  request('УЧ-001', 'open', 'Поставка оборудования · учебный пример', 'submitted'),
  request('УЧ-002', 'closed', 'Комплект материалов · учебный пример', 'accepted'),
];
const headings: Record<string, string> = {
  hierarchy: 'Иерархия объединений',
  'hierarchy-actions': 'Иерархия объединений',
  'requests-staff': 'Заявки',
  'requests-operator': 'Заявки',
  'requests-contractor': 'Мои заявки',
  'contractor-available': 'Актуальные заявки',
  users: 'Пользователи',
  'contractor-directory': 'Контрагенты',
  plan: 'План',
  process: 'Процесс работы',
};

const employee = {
  user_id: 'training-economist', role_id: ROLE.ECONOMIST, id_parent: null, status: 'active',
  full_name: 'Борис', phone: null, mail: 'training@example.invalid', company_name: null,
  inn: null, company_phone: null, company_mail: null, address: null, note: null,
  units_count: 1, managers_count: 2, subordinates_count: 1,
  actions: normalizeUserActions({ can_update_role: true, can_reset_password: true }),
};
const company: ContractorListItem = {
  userId: 'training-supplier', roleId: ROLE.CONTRACTOR, fullName: 'Контакт поставщика',
  companyName: 'Учебный поставщик', mail: 'supplier@example.invalid', emailVerified: true,
  status: view === 'registration-review' ? 'review' : 'active',
  inn: null, phone: null, companyPhone: null, companyMail: 'sales@example.invalid',
  address: null, note: null, createdAt: trainingDate, updatedAt: trainingDate, rootUnits: null,
  actions: normalizeUserActions({ can_update_status: true, can_manage_contractor_unit_bindings: true }),
};
const hierarchyUser = (member: UnitMember) => ({
  userId: member.user_id, fullName: member.full_name, roleId: member.role_id,
  roleName: member.role_name, status: member.status,
});
const hierarchyRelation = (node: UnitNode, index = 0) => ({
  ...hierarchyUser(node.members[index]), sourceUnitId: node.unit_id, sourceUnitName: node.name,
});
const branch = tree[0].children[0];
const employeeHierarchy = {
  user: hierarchyUser(branch.members[1]),
  units: [{ unitId: branch.unit_id, name: branch.name, parentUnitId: branch.id_parent }],
  managers: [hierarchyRelation(tree[0]), hierarchyRelation(branch)],
  subordinates: [hierarchyRelation(branch.children[0])],
  legacyHierarchy: { legacyManager: null, legacySubordinates: [], isBusinessSource: false, note: '' },
};

function PlanCreatePreview() {
  const rootPlanForm = useForm<RootPlanFormValues>({
    defaultValues: { name: 'Учебный план', periodStart: '2026-11-19', periodEnd: '2026-12-31', planAmount: '300000' },
  });
  const subplanForm = useForm<SubplanFormValues>();
  const delegateForm = useForm<DelegateFormValues>();
  const editForm = useForm<EditFormValues>();
  return <PlanDialogs isMutating={false} canCreateRootPlan rootDialogOpen
    subplanNode={null} delegateNode={null} delegateCandidates={[]} isCandidatesLoading={false}
    editNode={null} deleteNode={null} closeNode={null}
    rootPlanForm={rootPlanForm} subplanForm={subplanForm} delegateForm={delegateForm} editForm={editForm}
    onCloseRootDialog={noop} onCloseSubplanDialog={noop} onCloseDelegateDialog={noop}
    onCloseEditDialog={noop} onCloseDeleteDialog={noop} onCloseCloseDialog={noop}
    onSubmitRoot={noop} onSubmitSubplan={noop} onSubmitDelegate={noop} onSubmitEdit={noop}
    onConfirmDelete={noop} onConfirmClose={noop} />;
}

function Scene() {
  const { session } = useAuth();
  if (!session) return null;
  switch (view) {
    case 'hierarchy':
    case 'hierarchy-actions': {
      const withActions = view === 'hierarchy-actions';
      const editable = { ...branch, actions: { ...branch.actions, canCreateChild: true, canManageMembers: true } };
      return <UnitOrgChart tree={withActions ? [{ ...tree[0], children: [editable, tree[0].children[1]] }] : tree}
        onDelete={noop} onOpenCreateChildDialog={withActions ? noop : undefined}
        onOpenMemberDialog={withActions ? noop : undefined} showPrimaryActions={withActions} />;
    }
    case 'requests-staff':
    case 'requests-operator':
    case 'contractor-available':
    case 'requests-contractor': {
      const ownOffers = view === 'requests-contractor';
      const rows = view === 'requests-operator'
        ? [{ ...requests[0], id_user: 'training-operator', owner_full_name: 'Учебный оператор', count_submitted: 0, unread_messages_count: 0 }]
        : view === 'contractor-available' ? [{ ...requests[0], offers: [], unread_messages_count: 0 }] : requests;
      return <RequestsTable requests={rows} isContractor={contractor} showContractorOffersColumn={ownOffers}
        showContractorNotificationColumn={ownOffers} onRowClick={noop} />;
    }
    case 'employee-scope':
      return <EmployeeCardDialog open onClose={noop} user={employee} hierarchy={employeeHierarchy}
        unitsTree={tree} isLoadingHierarchy={false} />;
    case 'password':
      return <Box sx={{ maxWidth: 580 }}><PasswordChangeForm /></Box>;
    case 'file-preview':
      return <FilePreviewDialog source={{ name: documentName, downloadUrl: '/api/v1/files/1/download' }} onClose={noop} />;
    case 'notifications-staff':
    case 'contractor-notifications':
      return <Box sx={{ maxWidth: 510, minHeight: 220, bgcolor: 'background.paper' }}>
        <NotificationCenterPanel notifications={[{
          id: 1, type: contractor ? 'offer.accepted' : 'offer.created', severity: 'info',
          title: contractor ? 'Ваше КП принято' : 'Поступило новое КП',
          body: contractor ? 'Ваш отклик по заявке УЧ-001 принят.' : 'Новое предложение по заявке УЧ-001.',
          entity_type: 'offer', entity_id: 1, link_url: '/offers/1/workspace', payload: {},
          read_at: null, created_at: trainingDate,
        }]} hasUnread isLoading={false} isMarkAllPending={false} error={null} markingIds={new Set()}
          onClose={noop} onRetry={noop} onMarkAll={noop} onNotificationClick={noop}
          size={{ width: 510, height: 280 }} showResizeHandle={false}
          resizeHandleProps={{ onPointerDown: noop, onPointerMove: noop, onPointerUp: noop, onPointerCancel: noop, onDoubleClick: noop }} />
      </Box>;
    case 'chat-staff':
    case 'contractor-chat':
      return <Box sx={{ width: 460, height: 430 }}>
        <OfferWorkspaceChatPanel offerId={1} isOpen onToggleOpen={noop} sessionLogin={session.login}
          messages={[
            { id: 1, offer_id: 1, user_id: 'training-buyer', user_full_name: 'Контакт по заявке',
              text: 'Добрый день! Уточните, пожалуйста, срок поставки.', created_at: trainingDate, updated_at: trainingDate,
              status: 'read', read_by: [], attachments: [] },
            { id: 2, offer_id: 1, user_id: 'training-supplier', user_full_name: 'Контакт поставщика',
              text: 'Поставка займёт 10 рабочих дней.', created_at: '2026-11-19T09:05:00Z', updated_at: trainingDate,
              status: 'send', read_by: [], attachments: [] },
          ]} typingUserIds={[]} canSendMessage canSendMessageWithAttachments isSending={false}
          onSendMessage={asyncNoop} onMessageInputClick={noop} onMessageDraftChange={noop} onDownloadAttachment={noop} />
      </Box>;
    case 'request-create':
      return <CreateRequestPage />;
    case 'manual-offer':
      return <CreateManualOfferDialog open requestId="УЧ-001" onClose={noop} onCreated={noop} />;
    case 'offers-review':
    case 'assign-owner':
    case 'request-close':
      return <Routes><Route path="/requests/:id" element={<RequestDetailsView />} /></Routes>;
    case 'plan':
      return <PlanKpiRow totalPlanAmount={300000} totalFactAmount={150000}
        totalProgressPercent={50} totalRemainingAmount={150000} participantCount={3} />;
    case 'plan-create':
      return <PlanCreatePreview />;
    case 'process':
      return <CircularProcessChart totals={{ open: 4, review: 2 }} statusColors={{
        open: '#2e7d32', review: '#ed6c02',
      }} />;
    case 'contractor-directory':
    case 'registration-review':
      return <ContractorsListView contractors={[company]} emptyMessage="Нет контрагентов" onStatusUpdated={asyncNoop} />;
    case 'users':
    case 'admin-access':
      return <UsersTable users={[employee]} emptyMessage="Нет пользователей"
        getRoleLabel={(id) => id === ROLE.LEAD_ECONOMIST ? 'Ведущий экономист' : 'Экономист'}
        isContractorsTab={false} canViewRoleIds={false} canUpdateStatus canUpdateRole
        allowedRoleOptions={[ROLE.ECONOMIST, ROLE.LEAD_ECONOMIST]} onStatusUpdated={asyncNoop} />;
    case 'password-reset':
      return <UserPasswordResetButton userId={employee.user_id} canResetPassword />;
    case 'system':
      return <SystemStatusPage />;
    case 'invite':
      return <ContractorInviteDialog open onClose={noop} />;
    case 'feedback':
      return <FeedbackButton />;
    case 'normative':
      return <NormativeFilesPageView />;
    case 'contractor-respond':
      return <Routes><Route path="/requests/:id/contractor" element={<ContractorRequestDetailsPage />} /></Routes>;
    case 'contractor-edit':
    case 'contractor-files':
      return <Routes><Route path="/offers/:id/workspace" element={<OfferWorkspaceView />} /></Routes>;
    default:
      throw new Error(`Unknown documentation view: ${view}`);
  }
}

const selectedGuide = roleGuides[Number(params.get('role') ?? ROLE.ECONOMIST)];
const introGuide = {
  ...selectedGuide, sections: selectedGuide.sections.map((chapter) => ({
    ...chapter, blocks: chapter.blocks.filter((block) => block.type !== 'image'),
  })),
};
const route = view === 'contractor-respond' ? '/requests/УЧ-001/contractor'
  : view === 'contractor-edit' || view === 'contractor-files' ? '/offers/1/workspace' : '/requests/УЧ-001';
const compact = ['password', 'notifications-staff', 'contractor-notifications', 'chat-staff', 'contractor-chat'].includes(view);

createRoot(document.getElementById('root')!).render(
  <ThemeProvider theme={appTheme}><CssBaseline />
    {view === 'manifest' ? <pre id="guide-manifest">{JSON.stringify(roleGuides)}</pre>
      : view === 'guide' || view === 'intro' ? <RoleGuideDialog guide={view === 'intro' ? introGuide : selectedGuide} open onClose={noop} />
      : <MemoryRouter initialEntries={[route]}>
        <SnackbarProvider><AuthProvider><ChatRealtimeProvider><PageBreadcrumbActionsProvider>
          <Box data-guide-preview sx={{ p: 1.5, backgroundColor: 'background.default', width: '100%', maxWidth: compact ? 640 : undefined }}>
            <Stack spacing={2}>
              <Box><Typography variant="overline" color="primary">Учебные данные</Typography>
                {headings[view] && <Typography variant="h5" component="h1" fontWeight={700}>{headings[view]}</Typography>}
              </Box>
              <Scene />
            </Stack>
          </Box>
        </PageBreadcrumbActionsProvider></ChatRealtimeProvider></AuthProvider></SnackbarProvider>
      </MemoryRouter>}
  </ThemeProvider>,
);
