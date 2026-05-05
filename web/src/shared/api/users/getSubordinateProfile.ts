import { fetchJson } from '../client';
import type { UnavailabilityPeriodView } from '@entities/unavailability';
import { normalizeUserActions, type UserActions } from '../mappers';

type SubordinatePayload = {
  user_id: string;
  role_id: number;
  id_parent?: string | null;
  status: string;
  actions?: {
    can_view_profile?: boolean;
    can_update_status?: boolean;
    can_update_manager?: boolean;
    can_manage_subordinate_unavailability?: boolean;
  };
  full_name?: string | null;
  phone?: string | null;
  mail?: string | null;
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
};

type SubordinateResponse = {
  data: SubordinatePayload;
};

export type SubordinateProfile = {
  userId: string;
  roleId: number;
  parentUserId: string | null;
  status: string;
  fullName: string | null;
  phone: string | null;
  mail: string | null;
  unavailablePeriod: UnavailabilityPeriodView | null;
  unavailablePeriods: UnavailabilityPeriodView[];
  actions: UserActions;
};

type SetSubordinateUnavailabilityPayload = {
  status: string;
  started_at: string;
  ended_at: string;
};

const mapSubordinateProfile = (response: SubordinateResponse): SubordinateProfile => ({
  userId: response.data.user_id,
  roleId: response.data.role_id,
  parentUserId: response.data.id_parent ?? null,
  status: response.data.status,
  fullName: response.data.full_name ?? null,
  phone: response.data.phone ?? null,
  mail: response.data.mail ?? null,
  unavailablePeriod: response.data.unavailable_period
    ? {
        id: response.data.unavailable_period.id,
        status: response.data.unavailable_period.status,
        startedAt: response.data.unavailable_period.started_at,
        endedAt: response.data.unavailable_period.ended_at
      }
    : null,
  unavailablePeriods: (response.data.unavailable_periods ?? []).map((period) => ({
    id: period.id,
    status: period.status,
    startedAt: period.started_at,
    endedAt: period.ended_at
  })),
  actions: normalizeUserActions(response.data.actions)
});

export const getSubordinateProfile = async (userId: string): Promise<SubordinateProfile> => {
  const response = await fetchJson<SubordinateResponse>(
    `/api/v1/users/${userId}/profile`,
    { method: 'GET' },
    'Ошибка загрузки профиля подчинённого'
  );

  return mapSubordinateProfile(response);
};

export const setSubordinateUnavailabilityPeriod = async (
  userId: string,
  payload: SetSubordinateUnavailabilityPayload
): Promise<SubordinateProfile> => {
  const response = await fetchJson<SubordinateResponse>(
    `/api/v1/users/${userId}/unavailability-period`,
    { method: 'POST', body: JSON.stringify(payload) },
    'Ошибка обновления нерабочего статуса подчинённого'
  );

  return mapSubordinateProfile(response);
};
