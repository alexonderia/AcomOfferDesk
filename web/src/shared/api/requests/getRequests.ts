import { fetchJson } from '../client';
import { mapRequestEntityToSummary, normalizeOfferActions, type OfferActions, type RequestActions } from '../mappers';
import type { FileEntity, RequestEntity } from '@entities/request';

export type RequestFile = FileEntity;

export type ContractorRequestOffer = {
  id: number;
  status: string;
  unread_messages_count?: number;
  actions: OfferActions;
};

export type RequestWithOfferStats = {
  id: number;
  id_user: string;
  owner_full_name?: string | null;
  status: string;
  status_label: string;
  deadline_at: string;
  closed_at: string | null;
  id_offer: number | null;
  description: string | null;
  created_at: string;
  updated_at: string;
  count_submitted?: number;
  count_deleted_alert?: number;
  count_accepted_total?: number;
  count_rejected_total?: number;
  count_chat_alert?: number;
  unread_messages_count?: number;
  files: RequestFile[];
  actions: RequestActions;
  offers?: ContractorRequestOffer[];
};

export type GetRequestsResponse = {
  requests: RequestWithOfferStats[];
};

type ApiResponse = {
  data: {
    items: Array<RequestEntity & {
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
      offers?: Array<{
        id?: number;
        offer_id?: number;
        status: string;
        unread_messages_count?: number;
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
      }>;
    }>;
  };
};

export const mapContractorOfferSummary = (offer: {
  id?: number;
  offer_id?: number;
  status: string;
  unread_messages_count?: number;
  actions?: Parameters<typeof normalizeOfferActions>[0];
}): ContractorRequestOffer => ({
  id: offer.id ?? offer.offer_id ?? 0,
  status: offer.status,
  unread_messages_count: offer.unread_messages_count ?? 0,
  actions: normalizeOfferActions(offer.actions)
});

export const getRequests = async (): Promise<GetRequestsResponse> => {
  const response = await fetchJson<ApiResponse>(
    '/api/v1/requests',
    { method: 'GET' },
    'Ошибка загрузки заявок'
  );
  return {
    requests: response.data.items.map(mapRequestEntityToSummary)
  };
};
