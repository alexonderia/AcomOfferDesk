import { fetchJson } from '../client';
import { normalizeOfferActions, normalizeRequestActions, type OfferActions, type RequestActions } from '../mappers';
import type { FileEntity, RequestEntity } from '@entities/request';

export type RequestDetailsFile = FileEntity;

export type RequestDetailsOffer = {
  offer_id: number;
  status: string | null;
  offer_amount?: number | null;
  created_at: string;
  updated_at: string;
  status_label?: string | null;
  offer_workspace_url?: string | null;
  contractor_user_id?: string | null;
  contractor_company_name?: string | null;
  contractor_full_name?: string | null;
  contractor_phone?: string | null;
  contractor_mail?: string | null;
  contractor_address?: string | null;
  contractor_note?: string | null;
  contractor_inn?: string | null;
  contractor_company_phone?: string | null;
  contractor_company_mail?: string | null;
  contractor_contact_phone?: string | null;
  contractor_contact_mail?: string | null;
  unread_messages_count?: number | null;
  offer_chat_stats?: {
    status_web: boolean | null;
    status_tg: boolean | null;
    updated_at?: string | null;
  } | null;
  files: RequestDetailsFile[];
  actions: OfferActions;
};

export type RequestDetails = {
  id: number;
  id_user: string;
  owner_full_name?: string | null;
  status: string;
  status_label: string;
  initial_amount: number | null;
  final_amount: number | null;
  deadline_at: string;
  closed_at: string | null;
  id_offer: number | null;
  id_plan: number | null;
  description: string | null;
  created_at: string;
  updated_at: string;
  count_submitted: number;
  count_deleted_alert: number;
  count_accepted_total: number;
  count_rejected_total: number;
  files: RequestDetailsFile[];
  offers: RequestDetailsOffer[];
  actions: RequestActions;
};

type ApiRequestItem = RequestEntity & {
  actions?: {
    can_view_details?: boolean;
    can_view_amounts?: boolean;
    can_open_contractor_view?: boolean;
    can_edit?: boolean;
    can_change_owner?: boolean;
    can_upload_files?: boolean;
    can_delete_files?: boolean;
    can_send_email_notifications?: boolean;
    can_mark_deleted_alert_viewed?: boolean;
    can_create_offer?: boolean;
  };
  initial_amount?: number | null;
  final_amount?: number | null;
  files: RequestDetailsFile[];
  offers?: Array<
    Omit<RequestDetailsOffer, 'actions'> & {
      actions?: {
        can_open_workspace?: boolean;
        can_view_contractor_info?: boolean;
        can_edit_amount?: boolean;
        can_accept?: boolean;
        can_reject?: boolean;
        can_delete?: boolean;
        can_upload_files?: boolean;
        can_delete_files?: boolean;
      };
    }
  >;
};

type ApiResponse = {
  data: {
    item: ApiRequestItem;
  };
};

export const getRequestDetails = async (requestId: number): Promise<RequestDetails> => {
  const response = await fetchJson<ApiResponse>(
    `/api/v1/requests/${requestId}`,
    { method: 'GET' },
    'Ошибка загрузки заявки'
  );

  const item = response.data.item;

  return {
    id: item.request_id,
    id_user: item.owner_user_id,
    owner_full_name: item.owner_full_name ?? null,
    status: item.status,
    status_label: item.status_label,
    initial_amount: item.initial_amount ?? null,
    final_amount: item.final_amount ?? null,
    deadline_at: item.deadline_at,
    closed_at: item.closed_at,
    id_offer: item.chosen_offer_id,
    id_plan: item.id_plan ?? null,
    description: item.description,
    created_at: item.created_at,
    updated_at: item.updated_at,
    count_submitted: item.stats?.count_submitted ?? 0,
    count_deleted_alert: item.stats?.count_deleted_alert ?? 0,
    count_accepted_total: item.stats?.count_accepted_total ?? 0,
    count_rejected_total: item.stats?.count_rejected_total ?? 0,
    files: item.files ?? [],
    offers: (item.offers ?? []).map((offer) => ({
      ...offer,
      actions: normalizeOfferActions(offer.actions)
    })),
    actions: normalizeRequestActions(item.actions)
  };
};
