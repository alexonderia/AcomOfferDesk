// Read-only fixture responses for the browser used to capture the documentation.
const date = '2026-11-19T09:00:00Z';
const deadline = '2026-11-30T12:00:00Z';
const file = { id: 1, name: 'Учебная спецификация.png', path: 'example.png', download_url: '/api/v1/files/1/download' };
const request = {
  request_id: 'УЧ-001', status: 'open', status_label: 'Открыта',
  description: 'Поставка оборудования. В предложении укажите срок поставки и стоимость комплекта.',
  owner_user_id: 'training-buyer', owner_full_name: 'Контакт по заявке', created_at: date,
  updated_at: date, deadline_at: deadline, closed_at: null, files: [file],
};
const offer = {
  offer_id: 1, status: 'submitted', status_label: 'На рассмотрении', offer_amount: 850000,
  created_at: date, updated_at: date, files: [{ ...file, name: 'Предложение поставщика.png' }],
  actions: { can_open_workspace: true, can_edit_amount: true, can_delete: true, can_upload_files: true, can_delete_files: true },
};
const chat = { can_view_messages: true, can_send_message: true, can_attach_files: true };
const staffOffer = {
  ...offer, contractor_user_id: 'training-supplier', contractor_company_name: 'Учебный поставщик',
  contractor_status: 'active', actions: { can_open_workspace: true, can_accept: true, can_reject: true },
};
const company = { user_id: 'training-supplier', company_name: 'Учебный поставщик', full_name: 'Контакт поставщика', status: 'active', has_offer: false };
const staffPermissions = [
  'requests.create', 'requests.read', 'requests.update', 'normative_files.manage',
  'users.read', 'users.role.update_any', 'users.registration.approve', 'contractors.read',
  'offers.manual.create',
];
const responses = {
  '/api/v1/auth/csrf': { csrf_token: 'training-example' },
  '/api/v1/auth/capabilities': { data: { email_enabled: false }, email_enabled: false },
  '/api/v1/normative-files': { data: { items: [{
    id: 1, file_id: 1, original_name: file.name, status: 'actual', created_at: date, download_url: file.download_url,
  }] } },
  '/api/v1/requests/check-id': { available: true, detail: 'Номер свободен' },
  '/api/v1/users/request-contractors': { data: { items: [company] } },
  '/api/v1/requests/УЧ-001/offers/manual/eligible-contractors': { data: { items: [company] } },
  '/api/v1/requests/УЧ-001/eligible-owners': { data: { items: [
    { user_id: 'training-buyer', full_name: 'Контакт по заявке', role: 'economist', unavailable_period: null },
    { user_id: 'training-economist', full_name: 'Борис', role: 'economist', unavailable_period: null },
  ] } },
  '/api/v1/plans/options': { data: { items: [] } },
  '/api/v1/requests/УЧ-001/contractor-view': { data: {
    ...request, existing_offer: null, actions: { can_open_contractor_view: true, can_create_offer: true },
  } },
  '/api/v1/offers/1/workspace': { data: {
    request: { ...request, actions: { can_open_contractor_view: true } }, offer, chat_actions: chat,
  } },
  '/api/v1/offers/1/messages': { data: { offer_id: 1, items: [], actions: chat } },
  '/api/v1/contractors/login-access': { data: { items: [{
    user_id: company.user_id, state: 'available', label: 'Вход доступен', description: 'Учебный кабинет доступен.',
  }] } },
  '/api/v1/contractors/training-supplier/root-units': { data: {
    contractor_user_id: company.user_id, can_manage: true,
    items: [{ unit_id: 1, unit_name: 'Учебное подразделение', is_bound: true, can_manage: true }],
  } },
  '/api/v1/users/training-economist/hierarchy': { data: {
    user: { user_id: 'training-economist', full_name: 'Борис', role_id: 6, role_name: 'Экономист', status: 'active' },
    units: [{ unit_id: 2, name: 'Объединение А', id_parent: 1 }], managers: [], subordinates: [],
    legacy_hierarchy: { is_business_source: false, note: '' },
  } },
  '/api/v1/users/training-economist/hierarchy/units-tree': { data: { items: [] } },
  '/api/v1/users/training-economist/delegations/department': { data: {
    user_id: 'training-economist', role_id: 6, full_name: 'Борис', can_manage: true,
    accesses: [{
      code: 'department.requests.read', permission_code: 'department.requests.read', group: 'Заявки',
      label: 'Просмотр заявок подразделения', enabled: false, granted_via_role: false, granted_individually: false,
    }],
  } },
  '/api/v1/system/status': { data: {
    checked_at: date, overall: 'healthy', uptime_seconds: 3600, cache_ttl_seconds: 20, probe_timeout_seconds: 2,
    settings: { environment: 'Учебное окружение', email_enabled: false, smtp_configured: false, imap_configured: false,
      file_guard_enabled: true, secure_cookies: true, cookie_samesite: 'lax', signed_file_link_ttl_seconds: 300,
      websocket_ticket_ttl_seconds: 30 },
    services: ['Приложение', 'IAM', 'PostgreSQL', 'Хранилище документов', 'Проверка файлов'].map((name, index) => ({
      key: String(index), name, status: 'up', response_ms: index + 2, detail: 'Учебный результат проверки',
    })),
  } },
};

export function getGuideFixture(pathname, view) {
  if (pathname === '/api/v1/auth/session') {
    const contractor = view.startsWith('contractor-') && !['contractor-directory'].includes(view)
      || view === 'requests-contractor';
    const roleId = contractor ? 3 : ({ 'assign-owner': 4, 'requests-operator': 7, 'admin-access': 1, system: 1, invite: 8, 'registration-review': 8, normative: 5 })[view] ?? 6;
    const login = contractor ? 'training-supplier' : 'training-buyer';
    return { data: {
      user_id: login, login, role_id: roleId, role: contractor ? 'contractor' : 'employee',
      status: 'active', auth_provider: 'iam', business_access: true, onboarding_state: null,
      email_enabled: view === 'invite' || view === 'registration-review',
      permissions: contractor ? ['requests.contractor_view.read'] : staffPermissions,
    } };
  }
  if (pathname === '/api/v1/requests/УЧ-001') {
    const closing = view === 'request-close';
    return { data: { item: {
      ...request, initial_amount: 1000000, final_amount: closing ? 850000 : null,
      chosen_offer_id: closing ? 1 : null, stats: { count_submitted: closing ? 0 : 1 },
      offers: [closing ? { ...staffOffer, status: 'accepted', status_label: 'Принят' } : staffOffer],
      actions: { can_view_details: true, can_view_amounts: true, can_edit: true, can_update_status: true,
        can_change_owner: view === 'assign-owner', can_create_offer: view === 'offers-review' },
    } } };
  }
  if (pathname === '/api/v1/contractors/login-access' && view === 'registration-review') {
    return { data: { items: [{
      user_id: company.user_id, state: 'pending', label: 'Ожидает проверки', description: 'Регистрация ожидает проверки.',
    }] } };
  }
  return responses[pathname];
}
