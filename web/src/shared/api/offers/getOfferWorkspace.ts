import { fetchJson } from '../client';
import type { ContractorRequestViewFile } from '../requests/getContractorRequestView';
import { normalizeChatActions, normalizeOfferActions, normalizeRequestActions, type ChatActions, type OfferActions, type RequestActions } from '../mappers';

export type WorkspaceOfferItem = {
  offer_id: number;
  contractor_user_id?: string;
  status: string;
  status_label: string;
  offer_amount?: number | null;
  created_at: string | null;
  updated_at: string | null;
  files: ContractorRequestViewFile[];
  actions: OfferActions;
  selfHref?: string;
};

export type OfferWorkspace = {
  request: {
    request_id: number;
    description: string | null;
    status: string;
    status_label: string;
    chosen_offer_id?: number | null;
    id_offer?: number | null;
    owner_user_id?: string;
    owner_full_name?: string | null;
    initial_amount?: number | null;
    final_amount?: number | null;
    deadline_at: string;
    created_at: string | null;
    updated_at: string | null;
    closed_at: string | null;
    files: ContractorRequestViewFile[];
    actions: RequestActions;
  };
  offer: WorkspaceOfferItem;
  offers: WorkspaceOfferItem[];
  profile: {
    full_name: string;
    phone: string;
    mail: string;
  } | null;
  company_contacts: {
    company_name: string;
    inn: string;
    phone: string;
    mail: string;
    address: string;
    note: string;
  } | null;
  chatActions: ChatActions;
};

type ApiOfferItem = Omit<WorkspaceOfferItem, 'actions' | 'selfHref' | 'files'> & {
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
  files?: ContractorRequestViewFile[];
  _links?: {
    self?: {
      href: string;
    };
  };
};

type ApiResponse = {
  data: {
    request: Omit<OfferWorkspace['request'], 'actions'> & {
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
    offer: ApiOfferItem;
    offers?: ApiOfferItem[];
    chat_actions?: {
      can_view_messages?: boolean;
      can_send_message?: boolean;
      can_attach_files?: boolean;
      can_mark_messages_received?: boolean;
      can_mark_messages_read?: boolean;
    };
    contractor?: {
      user_id: string;
      full_name: string | null;
      phone: string | null;
      mail: string | null;
      company_name: string | null;
      inn: string | null;
      company_phone: string | null;
      company_mail: string | null;
      address: string | null;
      note: string | null;
    };
  };
};

const mapOfferItem = (offer: ApiOfferItem, contractorUserId?: string): WorkspaceOfferItem => ({
  offer_id: offer.offer_id,
  contractor_user_id: contractorUserId,
  status: offer.status,
  status_label: offer.status_label,
  offer_amount: offer.offer_amount ?? null,
  created_at: offer.created_at,
  updated_at: offer.updated_at,
  files: offer.files ?? [],
  actions: normalizeOfferActions(offer.actions),
  selfHref: offer._links?.self?.href
});

export const getOfferWorkspace = async (offerId: number): Promise<OfferWorkspace> => {
  const response = await fetchJson<ApiResponse>(
    `/api/v1/offers/${offerId}/workspace`,
    { method: 'GET' },
    'Ошибка загрузки рабочего пространства КП'
  );

  const contractorUserId = response.data.contractor?.user_id;
  const normalizedCurrentOffer = mapOfferItem(response.data.offer, contractorUserId);
  const normalizedOffers = (response.data.offers ?? []).map((offer) => mapOfferItem(offer, contractorUserId));

  return {
    request: {
      ...response.data.request,
      files: response.data.request.files ?? [],
      actions: normalizeRequestActions(response.data.request.actions)
    },
    offer: normalizedCurrentOffer,
    offers: normalizedOffers.length > 0 ? normalizedOffers : [normalizedCurrentOffer],
    profile: response.data.contractor
      ? {
          full_name: response.data.contractor.full_name ?? '',
          phone: response.data.contractor.phone ?? '',
          mail: response.data.contractor.mail ?? ''
        }
      : null,
    company_contacts: response.data.contractor
      ? {
          company_name: response.data.contractor.company_name ?? '',
          inn: response.data.contractor.inn ?? '',
          phone: response.data.contractor.company_phone ?? '',
          mail: response.data.contractor.company_mail ?? '',
          address: response.data.contractor.address ?? '',
          note: response.data.contractor.note ?? ''
        }
      : null,
    chatActions: normalizeChatActions(response.data.chat_actions)
  };
};
