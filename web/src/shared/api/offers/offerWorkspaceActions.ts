import { fetchEmpty, fetchJson } from '../client';
import { normalizeChatActions, type ChatActions } from '../mappers';
import type { OfferMessageEntity } from '@entities/offer';
import type { FileEntity } from '@entities/request';

export type OfferMessageAttachment = Pick<FileEntity, 'id' | 'name' | 'download_url'>;

export type OfferWorkspaceMessage = OfferMessageEntity & {
  offer_id: number;
  is_system?: boolean;
  is_muted?: boolean;
  attachments: OfferMessageAttachment[];
};

export type OfferMessagesResult = {
  offerId: number;
  items: OfferWorkspaceMessage[];
  actions: ChatActions;
};

type MessagesResponse = {
  data: {
    offer_id: number;
    items: Array<OfferWorkspaceMessage & { attachments?: OfferMessageAttachment[] }>;
    actions?: {
      can_view_messages?: boolean;
      can_send_message?: boolean;
      can_attach_files?: boolean;
      can_mark_messages_received?: boolean;
      can_mark_messages_read?: boolean;
    };
  };
};

type OfferMessageCreateResponse = {
  data: {
    offer_id: number;
    message_id: number;
  };
};

type UploadResponse = {
  data: {
    offer_id: number;
    file_id: number;
  };
};

type UpdateOfferAmountResponse = {
  data: {
    offer_id: number;
    offer_amount: number;
  };
};

type MessageFileUploadResponse = {
  data: {
    offer_id: number;
    file_id: number;
    name: string;
    path: string;
    upload_token: string;
    download_url: string;
  };
};

type MessageStatusPayload = {
  message_ids?: number[];
  up_to_message_id?: number;
};

type MessageStatusResponse = {
  data: {
    offer_id: number;
    updated_count: number;
  };
};

export const getOfferMessages = async (offerId: number): Promise<OfferMessagesResult> => {
  const response = await fetchJson<MessagesResponse>(
    `/api/v1/offers/${offerId}/messages`,
    { method: 'GET' },
    'Ошибка загрузки сообщений'
  );

  return {
    offerId: response.data.offer_id,
    items: (response.data.items ?? []).map((message) => ({
      ...message,
      offer_id: response.data.offer_id,
      read_by: message.read_by ?? [],
      attachments: message.attachments ?? []
    })),
    actions: normalizeChatActions(response.data.actions)
  };
};

export const sendOfferMessage = async (offerId: number, text: string): Promise<OfferMessageCreateResponse['data']> => {
  const response = await fetchJson<OfferMessageCreateResponse>(
    `/api/v1/offers/${offerId}/messages`,
    {
      method: 'POST',
      body: JSON.stringify({ text })
    },
    'Не удалось отправить сообщение'
  );

  return response.data;
};

export const sendOfferMessageWithAttachments = async (offerId: number, text: string, files: File[]) => {
  const formData = new FormData();
  formData.set('text', text);
  files.forEach((file) => {
    formData.append('files', file);
  });

  const response = await fetchJson<OfferMessageCreateResponse>(
    `/api/v1/offers/${offerId}/messages/attachments`,
    {
      method: 'POST',
      body: formData
    },
    'Не удалось отправить сообщение с вложениями'
  );

  return response.data;
};

export const markOfferMessagesReceived = async (offerId: number, messageIds: number[]) => {
  if (!messageIds.length) {
    return;
  }

  await fetchJson<MessageStatusResponse>(
    `/api/v1/offers/${offerId}/messages/received`,
    {
      method: 'PATCH',
      body: JSON.stringify({ message_ids: messageIds } satisfies MessageStatusPayload)
    },
    'Не удалось обновить статус доставки сообщений'
  );
};

export const markOfferMessagesRead = async (offerId: number, messageIds?: number[]) => {
  if (messageIds !== undefined && messageIds.length === 0) {
    return;
  }

  await fetchJson<MessageStatusResponse>(
    `/api/v1/offers/${offerId}/messages/read`,
    {
      method: 'PATCH',
      body: JSON.stringify(messageIds === undefined ? {} : ({ message_ids: messageIds } satisfies MessageStatusPayload))
    },
    'Не удалось обновить статус прочтения сообщений'
  );
};

export const uploadOfferFile = async (offerId: number, file: File) => {
  const formData = new FormData();
  formData.set('file', file);

  const response = await fetchJson<UploadResponse>(
    `/api/v1/offers/${offerId}/files`,
    {
      method: 'POST',
      body: formData
    },
    'Не удалось загрузить файл'
  );

  return response.data;
};

export const uploadOfferMessageFile = async (offerId: number, file: File) => {
  const formData = new FormData();
  formData.set('file', file);

  const response = await fetchJson<MessageFileUploadResponse>(
    `/api/v1/offers/${offerId}/messages/files`,
    {
      method: 'POST',
      body: formData
    },
    'Не удалось загрузить вложение для сообщения'
  );

  return response.data;
};

export const deleteOfferFile = async (offerId: number, fileId: number) => {
  await fetchEmpty(
    `/api/v1/offers/${offerId}/files/${fileId}`,
    { method: 'DELETE' },
    'Не удалось удалить файл'
  );
};

export const updateOfferAmount = async (offerId: number, offerAmount: number) => {
  const response = await fetchJson<UpdateOfferAmountResponse>(
    `/api/v1/offers/${offerId}`,
    {
      method: 'PATCH',
      body: JSON.stringify({ offer_amount: offerAmount })
    },
    'Не удалось сохранить сумму КП'
  );

  return response.data;
};
