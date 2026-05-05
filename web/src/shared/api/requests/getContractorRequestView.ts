import { fetchJson } from '../client';
import { normalizeOfferActions, normalizeRequestActions, type OfferActions, type RequestActions } from '../mappers';

export type ContractorRequestViewFile = {
  id: number;
  path: string;
  name: string;
  download_url: string;
};

export type ContractorExistingOffer = {
  offer_id: number;
  status: string;
  status_label: string;
  files: ContractorRequestViewFile[];
  actions: OfferActions;
};

export type ContractorRequestView = {
  id: number;
  description: string | null;
  status: string;
  status_label: string;
  deadline_at: string;
  updated_at?: string | null;
  owner_user_id: string;
  owner_full_name?: string | null;
  files: ContractorRequestViewFile[];
  existing_offer: ContractorExistingOffer | null;
  actions: RequestActions;
};

type ApiResponse = {
  data: {
    request_id: number;
    description: string | null;
    status: string;
    status_label: string;
    deadline_at: string;
    updated_at?: string | null;
    owner_user_id: string;
    owner_full_name?: string | null;
    files: ContractorRequestViewFile[];
    existing_offer: {
      offer_id: number;
      status: string;
      status_label: string;
      files: ContractorRequestViewFile[];
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
    } | null;
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
  };
};

export const getContractorRequestView = async (requestId: number): Promise<ContractorRequestView> => {
  const response = await fetchJson<ApiResponse>(
    `/api/v1/requests/${requestId}/contractor-view`,
    { method: 'GET' },
    'Ошибка загрузки заявки'
  );

  return {
    id: response.data.request_id,
    description: response.data.description,
    status: response.data.status,
    status_label: response.data.status_label,
    deadline_at: response.data.deadline_at,
    updated_at: response.data.updated_at ?? null,
    owner_user_id: response.data.owner_user_id,
    owner_full_name: response.data.owner_full_name ?? null,
    files: response.data.files ?? [],
    existing_offer: response.data.existing_offer
      ? {
          ...response.data.existing_offer,
          actions: normalizeOfferActions(response.data.existing_offer.actions)
        }
      : null,
    actions: normalizeRequestActions(response.data.actions)
  };
};
