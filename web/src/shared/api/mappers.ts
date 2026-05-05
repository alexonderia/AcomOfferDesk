import type { RequestEntity } from '@entities/request';
import type { RequestWithOfferStats } from './requests/getRequests';

type BackendRequestActionFlags = {
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

type BackendOfferActionFlags = {
  can_open_workspace?: boolean;
  can_view_contractor_info?: boolean;
  can_edit_amount?: boolean;
  can_accept?: boolean;
  can_reject?: boolean;
  can_delete?: boolean;
  can_upload_files?: boolean;
  can_delete_files?: boolean;
};

type BackendChatActionFlags = {
  can_view_messages?: boolean;
  can_send_message?: boolean;
  can_attach_files?: boolean;
  can_mark_messages_received?: boolean;
  can_mark_messages_read?: boolean;
};

type BackendUserActionFlags = {
  can_view_profile?: boolean;
  can_update_status?: boolean;
  can_update_role?: boolean;
  can_update_manager?: boolean;
  can_manage_own_profile?: boolean;
  can_manage_credentials?: boolean;
  can_manage_company_contacts?: boolean;
  can_manage_own_unavailability?: boolean;
  can_manage_subordinate_unavailability?: boolean;
  can_manage_manual_contractor?: boolean;
};

export type RequestActions = {
  view_details: boolean;
  view_amounts: boolean;
  open_contractor_view: boolean;
  edit: boolean;
  change_owner: boolean;
  upload_file: boolean;
  delete_file: boolean;
  send_email_notifications: boolean;
  mark_deleted_alert_viewed: boolean;
  create_offer: boolean;
};

export type OfferActions = {
  open_workspace: boolean;
  view_contractor_info: boolean;
  edit_amount: boolean;
  accept: boolean;
  reject: boolean;
  delete: boolean;
  upload_file: boolean;
  delete_file: boolean;
};

export type ChatActions = {
  view_messages: boolean;
  send_message: boolean;
  attach_file: boolean;
  mark_messages_received: boolean;
  mark_messages_read: boolean;
};

export type UserActions = {
  view_profile: boolean;
  update_status: boolean;
  update_role: boolean;
  update_manager: boolean;
  manage_own_profile: boolean;
  manage_credentials: boolean;
  manage_company_contacts: boolean;
  manage_own_unavailability: boolean;
  manage_subordinate_unavailability: boolean;
  manage_manual_contractor: boolean;
};

export const normalizeRequestActions = (actions?: BackendRequestActionFlags): RequestActions => ({
  view_details: Boolean(actions?.can_view_details),
  view_amounts: Boolean(actions?.can_view_amounts),
  open_contractor_view: Boolean(actions?.can_open_contractor_view),
  edit: Boolean(actions?.can_edit),
  change_owner: Boolean(actions?.can_change_owner),
  upload_file: Boolean(actions?.can_upload_files),
  delete_file: Boolean(actions?.can_delete_files),
  send_email_notifications: Boolean(actions?.can_send_email_notifications),
  mark_deleted_alert_viewed: Boolean(actions?.can_mark_deleted_alert_viewed),
  create_offer: Boolean(actions?.can_create_offer)
});

export const normalizeOfferActions = (actions?: BackendOfferActionFlags): OfferActions => ({
  open_workspace: Boolean(actions?.can_open_workspace),
  view_contractor_info: Boolean(actions?.can_view_contractor_info),
  edit_amount: Boolean(actions?.can_edit_amount),
  accept: Boolean(actions?.can_accept),
  reject: Boolean(actions?.can_reject),
  delete: Boolean(actions?.can_delete),
  upload_file: Boolean(actions?.can_upload_files),
  delete_file: Boolean(actions?.can_delete_files)
});

export const normalizeChatActions = (actions?: BackendChatActionFlags): ChatActions => ({
  view_messages: Boolean(actions?.can_view_messages),
  send_message: Boolean(actions?.can_send_message),
  attach_file: Boolean(actions?.can_attach_files),
  mark_messages_received: Boolean(actions?.can_mark_messages_received),
  mark_messages_read: Boolean(actions?.can_mark_messages_read)
});

export const normalizeUserActions = (actions?: BackendUserActionFlags): UserActions => ({
  view_profile: Boolean(actions?.can_view_profile),
  update_status: Boolean(actions?.can_update_status),
  update_role: Boolean(actions?.can_update_role),
  update_manager: Boolean(actions?.can_update_manager),
  manage_own_profile: Boolean(actions?.can_manage_own_profile),
  manage_credentials: Boolean(actions?.can_manage_credentials),
  manage_company_contacts: Boolean(actions?.can_manage_company_contacts),
  manage_own_unavailability: Boolean(actions?.can_manage_own_unavailability),
  manage_subordinate_unavailability: Boolean(actions?.can_manage_subordinate_unavailability),
  manage_manual_contractor: Boolean(actions?.can_manage_manual_contractor)
});

export const mapRequestEntityToSummary = (
  item: RequestEntity & {
    actions?: BackendRequestActionFlags;
    offers?: Array<{
      id?: number;
      offer_id?: number;
      status: string;
      unread_messages_count?: number;
      actions?: BackendOfferActionFlags;
    }>;
  }
): RequestWithOfferStats => ({
  id: item.request_id,
  id_user: item.owner_user_id,
  owner_full_name: item.owner_full_name ?? null,
  status: item.status,
  status_label: item.status_label,
  deadline_at: item.deadline_at,
  closed_at: item.closed_at,
  id_offer: item.chosen_offer_id,
  description: item.description,
  created_at: item.created_at,
  updated_at: item.updated_at,
  count_submitted: item.stats?.count_submitted ?? 0,
  count_deleted_alert: item.stats?.count_deleted_alert ?? 0,
  count_accepted_total: item.stats?.count_accepted_total ?? 0,
  count_rejected_total: item.stats?.count_rejected_total ?? 0,
  count_chat_alert: item.stats?.count_chat_alert ?? 0,
  unread_messages_count: item.unread_messages_count ?? 0,
  files: item.files,
  actions: normalizeRequestActions(item.actions),
  offers: item.offers?.map((offer) => ({
    id: offer.id ?? offer.offer_id ?? 0,
    status: offer.status,
    unread_messages_count: offer.unread_messages_count ?? 0,
    actions: normalizeOfferActions(offer.actions)
  }))
});
