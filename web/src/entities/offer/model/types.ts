import type { EntityId } from '@entities/request';

export type OfferStatus = 'submitted' | 'deleted' | 'accepted' | 'rejected';
export type MessageStatus = 'send' | 'received' | 'read';

export type OfferMessageReader = {
  user_id: string;
  user_full_name: string | null;
  read_at: string;
};

export type OfferMessageEntity = {
  id: EntityId;
  user_id: string;
  user_full_name: string | null;
  text: string;
  created_at: string;
  updated_at: string;
  status: MessageStatus;
  read_by: OfferMessageReader[];
};
