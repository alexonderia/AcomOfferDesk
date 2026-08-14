import { fetchJson } from '../client';
import { normalizeUserActions, type UserActions } from '../mappers';

type ProfilePayload = {
  user_id?: string;
  id?: string;
  role_id?: number;
  id_role?: number;
  status?: string;
  full_name?: string | null;
  phone?: string | null;
  mail?: string | null;
  company_name?: string | null;
  inn?: string | null;
  company_phone?: string | null;
  phone_company?: string | null;
  company_mail?: string | null;
  mail_company?: string | null;
  address?: string | null;
  note?: string | null;
  department_name?: string | null;
  permissions?: string[];
  identity_roles?: string[];
  app_roles?: string[];
  delegation_roles?: string[];
  actions?: {
    can_manage_own_profile?: boolean;
    can_manage_credentials?: boolean;
    can_manage_company_contacts?: boolean;
    can_manage_own_unavailability?: boolean;
  };
  unavailable_period?: {
    id: number;
    status: string;
    started_at: string;
    ended_at: string;
  } | null;
  unavailable_periods?: Array<{
    id: number;
    status: string;
    started_at: string;
    ended_at: string;
  }>;
  users?: {
    id?: string;
    user_id?: string;
    role_id?: number;
    id_role?: number;
    status?: string;
  };
  profiles?: {
    full_name?: string | null;
    phone?: string | null;
    mail?: string | null;
  };
  company_contacts?: {
    company_name?: string | null;
    inn?: string | null;
    phone?: string | null;
    mail?: string | null;
    address?: string | null;
    note?: string | null;
  };
};

type CurrentUserResponse = {
  data?: ProfilePayload;
};

type NotificationPreferencesPayload = {
  mode?: string;
  email_available?: boolean;
  email?: string | null;
  preferences?: Record<string, { email?: boolean }>;
};

type NotificationPreferencesResponse = {
  data?: NotificationPreferencesPayload;
};

export type CurrentUserProfile = {
  userId: string;
  roleId: number;
  status: string;
  fullName: string | null;
  phone: string | null;
  mail: string | null;
  departmentName: string | null;
  company: {
    companyName: string | null;
    inn: string | null;
    phone: string | null;
    mail: string | null;
    address: string | null;
    note: string | null;
  };
  unavailablePeriod: {
    id: number;
    status: string;
    startedAt: string;
    endedAt: string;
  } | null;
  unavailablePeriods: Array<{
    id: number;
    status: string;
    startedAt: string;
    endedAt: string;
  }>;
  permissions: string[];
  identityRoles: string[];
  appRoles: string[];
  delegationRoles: string[];
  actions: UserActions;
};

export type NotificationPreferencesMode = 'email_only' | 'none' | 'custom';

export type NotificationPreferenceType = 'chat' | 'request' | 'offer' | 'system';

export type NotificationPreferences = {
  mode: NotificationPreferencesMode;
  emailAvailable: boolean;
  email: string | null;
  preferences: Record<NotificationPreferenceType, { email: boolean }>;
};

type UpdateCredentialsPayload = {
  current_password: string;
  new_password: string;
};

type UpdateProfilePayload = {
  full_name?: string;
  phone?: string;
  mail?: string;
};

type SetUnavailabilityPeriodPayload = {
  status: string;
  started_at: string;
  ended_at: string;
};

type UpdateCompanyContactsPayload = {
  company_name?: string;
  inn?: string;
  company_phone?: string;
  company_mail?: string;
  address?: string;
  note?: string;
};

type UpdateNotificationPreferencesPayload = {
  mode?: Exclude<NotificationPreferencesMode, 'custom'>;
  preferences?: Partial<Record<NotificationPreferenceType, { email?: boolean }>>;
};

const mapCurrentUserProfile = (response: CurrentUserResponse): CurrentUserProfile => {
  const data = response.data ?? {};
  const users = data.users;
  const profiles = data.profiles;
  const companyContacts = data.company_contacts;

  return {
    userId: data.user_id ?? data.id ?? users?.user_id ?? users?.id ?? '',
    roleId: data.role_id ?? data.id_role ?? users?.role_id ?? users?.id_role ?? 0,
    status: data.status ?? users?.status ?? 'review',
    fullName: data.full_name ?? profiles?.full_name ?? null,
    phone: data.phone ?? profiles?.phone ?? null,
    mail: data.mail ?? profiles?.mail ?? null,
    departmentName: data.department_name ?? null,
    company: {
      companyName: data.company_name ?? companyContacts?.company_name ?? null,
      inn: data.inn ?? companyContacts?.inn ?? null,
      phone: data.company_phone ?? data.phone_company ?? companyContacts?.phone ?? null,
      mail: data.company_mail ?? data.mail_company ?? companyContacts?.mail ?? null,
      address: data.address ?? companyContacts?.address ?? null,
      note: data.note ?? companyContacts?.note ?? null
    },
    unavailablePeriod: data.unavailable_period
      ? {
          id: data.unavailable_period.id,
          status: data.unavailable_period.status,
          startedAt: data.unavailable_period.started_at,
          endedAt: data.unavailable_period.ended_at
        }
      : null,
    unavailablePeriods: (data.unavailable_periods ?? []).map((period) => ({
      id: period.id,
      status: period.status,
      startedAt: period.started_at,
      endedAt: period.ended_at
    })),
    permissions: data.permissions ?? [],
    identityRoles: data.identity_roles ?? [],
    appRoles: data.app_roles ?? [],
    delegationRoles: data.delegation_roles ?? [],
    actions: normalizeUserActions(data.actions)
  };
};

const mapNotificationPreferences = (response: NotificationPreferencesResponse): NotificationPreferences => {
  const data = response.data ?? {};
  const mode = data.mode;
  return {
    mode:
      mode === 'email_only' || mode === 'none' || mode === 'custom'
        ? mode
        : 'none',
    emailAvailable: Boolean(data.email_available),
    email: data.email ?? null,
    preferences: {
      chat: {
        email: Boolean(data.preferences?.chat?.email)
      },
      request: {
        email: Boolean(data.preferences?.request?.email)
      },
      offer: {
        email: Boolean(data.preferences?.offer?.email)
      },
      system: {
        email: Boolean(data.preferences?.system?.email)
      }
    }
  };
};

export const getCurrentUserProfile = async (): Promise<CurrentUserProfile> => {
  const response = await fetchJson<CurrentUserResponse>(
    '/api/v1/users/me',
    { method: 'GET' },
    'Ошибка загрузки профиля пользователя'
  );

  return mapCurrentUserProfile(response);
};

export const getRegistrationCurrentUserProfile = async (): Promise<CurrentUserProfile> => {
  const response = await fetchJson<CurrentUserResponse>(
    '/api/v1/users/me/registration-profile',
    { method: 'GET' },
    'Ошибка загрузки данных регистрации'
  );

  return mapCurrentUserProfile(response);
};

export const updateMyCredentials = async (payload: UpdateCredentialsPayload): Promise<CurrentUserProfile> => {
  const response = await fetchJson<CurrentUserResponse>(
    '/api/v1/users/me/credentials',
    { method: 'PATCH', body: JSON.stringify(payload) },
    'Ошибка обновления пароля'
  );

  return mapCurrentUserProfile(response);
};

export const updateMyProfile = async (payload: UpdateProfilePayload): Promise<CurrentUserProfile> => {
  const response = await fetchJson<CurrentUserResponse>(
    '/api/v1/users/me/profile',
    { method: 'PATCH', body: JSON.stringify(payload) },
    'Ошибка обновления личных данных'
  );

  return mapCurrentUserProfile(response);
};

export const getMyNotificationPreferences = async (): Promise<NotificationPreferences> => {
  const response = await fetchJson<NotificationPreferencesResponse>(
    '/api/v1/users/me/notification-preferences',
    { method: 'GET' },
    'Не удалось загрузить настройки уведомлений'
  );

  return mapNotificationPreferences(response);
};

export const updateMyNotificationPreferences = async (
  payload: UpdateNotificationPreferencesPayload
): Promise<NotificationPreferences> => {
  const response = await fetchJson<NotificationPreferencesResponse>(
    '/api/v1/users/me/notification-preferences',
    { method: 'PUT', body: JSON.stringify(payload) },
    'Не удалось сохранить настройки уведомлений'
  );

  return mapNotificationPreferences(response);
};

export const updateMyRegistrationProfile = async (payload: UpdateProfilePayload): Promise<CurrentUserProfile> => {
  const response = await fetchJson<CurrentUserResponse>(
    '/api/v1/users/me/registration-profile',
    { method: 'PATCH', body: JSON.stringify(payload) },
    'Ошибка обновления данных регистрации'
  );

  return mapCurrentUserProfile(response);
};

export const updateMyCompanyContacts = async (payload: UpdateCompanyContactsPayload): Promise<CurrentUserProfile> => {
  const response = await fetchJson<CurrentUserResponse>(
    '/api/v1/users/me/company-contacts',
    { method: 'PATCH', body: JSON.stringify(payload) },
    'Ошибка обновления данных компании'
  );

  return mapCurrentUserProfile(response);
};

export const updateMyRegistrationCompanyContacts = async (
  payload: UpdateCompanyContactsPayload
): Promise<CurrentUserProfile> => {
  const response = await fetchJson<CurrentUserResponse>(
    '/api/v1/users/me/registration-company-contacts',
    { method: 'PATCH', body: JSON.stringify(payload) },
    'Ошибка обновления данных компании при регистрации'
  );

  return mapCurrentUserProfile(response);
};

export const setMyUnavailabilityPeriod = async (payload: SetUnavailabilityPeriodPayload): Promise<CurrentUserProfile> => {
  const response = await fetchJson<CurrentUserResponse>(
    '/api/v1/users/me/unavailability-period',
    { method: 'POST', body: JSON.stringify(payload) },
    'Ошибка обновления нерабочего статуса'
  );

  return mapCurrentUserProfile(response);
};
