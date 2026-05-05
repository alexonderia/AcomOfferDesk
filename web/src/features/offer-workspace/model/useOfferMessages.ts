import { useCallback, useEffect, useRef, useState } from 'react';
import {
  getOfferMessages,
  markOfferMessagesRead,
  markOfferMessagesReceived,
  type OfferMessagesResult,
  type OfferWorkspaceMessage,
  uploadOfferMessageFile
} from '@shared/api/offers/offerWorkspaceActions';
import type { ChatActions } from '@shared/api/mappers';
import { getErrorMessage } from '@shared/lib/errors';
import type { ChatRealtimeEnvelope, RealtimeConnectionState } from '@shared/ws/chatSocket';

const TYPING_STOP_DELAY_MS = 2500;

type OfferMessagesByOfferId = Map<number, OfferMessagesResult>;

const loadOfferMessagesMap = async (
  offers: Array<{ offer_id: number; status: string; created_at: string | null; updated_at: string | null }>,
  preloadedResponses: OfferMessagesByOfferId = new Map()
) => {
  const missingOffers = offers.filter((offer) => !preloadedResponses.has(offer.offer_id));
  if (missingOffers.length === 0) {
    return preloadedResponses;
  }

  const loadedResponses = await Promise.all(
    missingOffers.map(async (offer) => [offer.offer_id, await getOfferMessages(offer.offer_id)] as const)
  );

  const responsesByOfferId = new Map(preloadedResponses);
  loadedResponses.forEach(([offerId, response]) => {
    responsesByOfferId.set(offerId, response);
  });
  return responsesByOfferId;
};

export const buildUnifiedChat = async (
  offers: Array<{ offer_id: number; status: string; created_at: string | null; updated_at: string | null }>,
  preloadedResponses: OfferMessagesByOfferId = new Map()
) => {
  const sortedByCreated = [...offers].sort(
    (left, right) => new Date(left.created_at ?? 0).getTime() - new Date(right.created_at ?? 0).getTime()
  );
  const responsesByOfferId = await loadOfferMessagesMap(sortedByCreated, preloadedResponses);
  const merged: OfferWorkspaceMessage[] = [];

  for (let idx = 0; idx < sortedByCreated.length; idx += 1) {
    const offer = sortedByCreated[idx];
    const response = responsesByOfferId.get(offer.offer_id);
    if (!response) {
      continue;
    }
    merged.push(
      ...response.items.map((message: OfferWorkspaceMessage) => ({
        ...message,
        offer_id: offer.offer_id,
        is_muted: offer.status === 'deleted'
      }))
    );

    if (offer.status === 'deleted') {
      merged.push({
        id: -1000000 - offer.offer_id,
        offer_id: offer.offer_id,
        user_id: 'system',
        user_full_name: 'Система',
        text: `КП №${offer.offer_id} было удалено.`,
        status: 'read',
        created_at: offer.updated_at ?? offer.created_at ?? new Date().toISOString(),
        updated_at: offer.updated_at ?? offer.created_at ?? new Date().toISOString(),
        read_by: [],
        attachments: [],
        is_system: true,
        is_muted: true
      });
      const nextOffer = sortedByCreated[idx + 1];
      if (nextOffer) {
        merged.push({
          id: -2000000 - nextOffer.offer_id,
          offer_id: nextOffer.offer_id,
          user_id: 'system',
          user_full_name: 'Система',
          text: `Создано новое КП №${nextOffer.offer_id}.`,
          status: 'read',
          created_at: nextOffer.created_at ?? new Date().toISOString(),
          updated_at: nextOffer.created_at ?? new Date().toISOString(),
          read_by: [],
          attachments: [],
          is_system: true,
          is_muted: false
        });
      }
    }
  }

  return {
    merged: merged.sort((a, b) => new Date(a.created_at ?? 0).getTime() - new Date(b.created_at ?? 0).getTime()),
    responsesByOfferId
  };
};

type UseOfferMessagesParams = {
  activeOfferId: number;
  offerItems: Array<{ offer_id: number; status: string; created_at: string | null; updated_at: string | null }>;
  sessionLogin?: string;
  connectionState: RealtimeConnectionState;
  onRealtimeEvent: (listener: (event: ChatRealtimeEnvelope) => void) => () => void;
  realtimeClient: {
    sendMessage: (chatId: number, text: string, files: Array<{ file_id: number; upload_token: string }>) => Promise<unknown>;
    markRead: (chatId: number, params: { messageIds?: number[]; upToMessageId?: number | null }) => Promise<unknown>;
    typingStart: (chatId: number) => Promise<unknown>;
    typingStop: (chatId: number) => Promise<unknown>;
    syncChat: (chatId: number, lastKnownMessageId?: number | null) => Promise<unknown>;
  };
};

export const useOfferMessages = ({
  activeOfferId,
  offerItems,
  sessionLogin,
  connectionState,
  onRealtimeEvent,
  realtimeClient
}: UseOfferMessagesParams) => {
  const [messages, setMessages] = useState<OfferWorkspaceMessage[]>([]);
  const [chatActions, setChatActions] = useState<ChatActions>({
    view_messages: false,
    send_message: false,
    attach_file: false,
    mark_messages_received: false,
    mark_messages_read: false
  });
  const [isSending, setIsSending] = useState(false);
  const [chatErrorMessage, setChatErrorMessage] = useState<string | null>(null);
  const [typingUserIds, setTypingUserIds] = useState<string[]>([]);

  const activeOfferIdRef = useRef(activeOfferId);
  const offerItemsRef = useRef(offerItems);
  const typingStopTimerRef = useRef<number | null>(null);
  const ownTypingActiveRef = useRef(false);
  const typingUsersTimeoutsRef = useRef<Map<string, number>>(new Map());

  useEffect(() => {
    activeOfferIdRef.current = activeOfferId;
  }, [activeOfferId]);

  useEffect(() => {
    offerItemsRef.current = offerItems;
  }, [offerItems]);

  const loadMessages = useCallback(async (offerId: number, nextOfferItems: typeof offerItems, syncStatuses = true) => {
    const messagesResponse = await getOfferMessages(offerId);
    const { merged } = await buildUnifiedChat(
      nextOfferItems,
      new Map<number, OfferMessagesResult>([[offerId, messagesResponse]])
    );
    setMessages(merged);
    setChatActions(messagesResponse.actions);

    if (!syncStatuses || !sessionLogin) {
      return;
    }

    const canSetReceived = messagesResponse.actions.mark_messages_received;

    const incomingSendIds = messagesResponse.items.filter((item) => item.user_id !== sessionLogin && item.status === 'send').map((item) => item.id);
    if (canSetReceived && incomingSendIds.length > 0) {
      if (connectionState === 'connected') {
        await realtimeClient.syncChat(offerId, messagesResponse.items[messagesResponse.items.length - 1]?.id ?? null);
      } else {
        await markOfferMessagesReceived(offerId, incomingSendIds);
        const refreshed = await getOfferMessages(offerId);
        const { merged } = await buildUnifiedChat(
          nextOfferItems,
          new Map<number, OfferMessagesResult>([[offerId, refreshed]])
        );
        setMessages(merged);
        setChatActions(refreshed.actions);
      }
    }
  }, [connectionState, realtimeClient, sessionLogin]);

  const mergeRealtimeMessage = useCallback((message: OfferWorkspaceMessage) => {
    const normalizedMessage: OfferWorkspaceMessage = {
      ...message,
      read_by: message.read_by ?? []
    };
    setMessages((current: OfferWorkspaceMessage[]) => {
      const existingIndex = current.findIndex((item) => item.id === normalizedMessage.id);
      if (existingIndex >= 0) {
        const next = [...current];
        next[existingIndex] = { ...next[existingIndex], ...normalizedMessage };
        return next;
      }
      return [...current, normalizedMessage].sort((a, b) => new Date(a.created_at ?? 0).getTime() - new Date(b.created_at ?? 0).getTime());
    });
  }, []);

  const updateMessageStatuses = useCallback((messageIds: number[], status: OfferWorkspaceMessage['status']) => {
    setMessages((current: OfferWorkspaceMessage[]) => current.map((message) => (
      messageIds.includes(message.id) && message.user_id === sessionLogin
        ? { ...message, status }
        : message
    )));
  }, [sessionLogin]);

  const appendMessageReaders = useCallback((params: {
    messageIds: number[];
    userId: string;
    userFullName?: string | null;
    readAt: string;
  }) => {
    setMessages((current: OfferWorkspaceMessage[]) => current.map((message) => {
      if (!params.messageIds.includes(message.id) || message.user_id !== sessionLogin) {
        return message;
      }

      const existingReaderIndex = message.read_by.findIndex((reader) => reader.user_id === params.userId);
      if (existingReaderIndex >= 0) {
        const nextReadBy = [...message.read_by];
        nextReadBy[existingReaderIndex] = {
          ...nextReadBy[existingReaderIndex],
          user_full_name: params.userFullName ?? nextReadBy[existingReaderIndex].user_full_name,
          read_at: params.readAt
        };
        return { ...message, read_by: nextReadBy };
      }

      return {
        ...message,
        read_by: [
          ...message.read_by,
          {
            user_id: params.userId,
            user_full_name: params.userFullName ?? null,
            read_at: params.readAt
          }
        ]
      };
    }));
  }, [sessionLogin]);

  useEffect(() => {
    const unsubscribe = onRealtimeEvent((event) => {
      if (event.type === 'message.created' && event.data.chat_id === activeOfferIdRef.current) {
        mergeRealtimeMessage(event.data.message as OfferWorkspaceMessage);
        return;
      }

      if (event.type === 'message.delivered' && event.data.chat_id === activeOfferIdRef.current) {
        updateMessageStatuses(event.data.message_ids, 'received');
        return;
      }

      if (event.type === 'message.read' && event.data.chat_id === activeOfferIdRef.current) {
        updateMessageStatuses(event.data.message_ids, 'read');
        appendMessageReaders({
          messageIds: event.data.message_ids,
          userId: event.data.user_id,
          userFullName: event.data.user_full_name ?? null,
          readAt: event.ts
        });
        return;
      }

      if ((event.type === 'typing.start' || event.type === 'typing.stop') && event.data.chat_id === activeOfferIdRef.current && event.data.user_id !== sessionLogin) {
        const key = `${event.data.chat_id}:${event.data.user_id}`;
        const timeoutMap = typingUsersTimeoutsRef.current;
        const existingTimeoutId = timeoutMap.get(key);
        if (existingTimeoutId) {
          window.clearTimeout(existingTimeoutId);
          timeoutMap.delete(key);
        }

        if (event.type === 'typing.start') {
          setTypingUserIds((current: string[]) => current.includes(event.data.user_id) ? current : [...current, event.data.user_id]);
          const timeoutId = window.setTimeout(() => {
            setTypingUserIds((current: string[]) => current.filter((item) => item !== event.data.user_id));
            timeoutMap.delete(key);
          }, TYPING_STOP_DELAY_MS);
          timeoutMap.set(key, timeoutId);
        } else {
          setTypingUserIds((current: string[]) => current.filter((item) => item !== event.data.user_id));
        }
        return;
      }

      if (event.type === 'chat.sync' && event.data.chat_id === activeOfferIdRef.current && event.data.resync_required) {
        void loadMessages(activeOfferIdRef.current, offerItemsRef.current, false).catch(() => undefined);
      }
    });

    return unsubscribe;
  }, [appendMessageReaders, loadMessages, mergeRealtimeMessage, onRealtimeEvent, sessionLogin, updateMessageStatuses]);

  useEffect(() => {
    return () => {
      if (typingStopTimerRef.current !== null) {
        window.clearTimeout(typingStopTimerRef.current);
      }
      typingUsersTimeoutsRef.current.forEach((timeoutId: number) => window.clearTimeout(timeoutId));
      typingUsersTimeoutsRef.current.clear();
    };
  }, []);

  const handleSendMessage = useCallback(async (params: {
    offerId: number;
    text: string;
    files: File[];
    canSendMessage: boolean;
  }) => {
    if (!params.canSendMessage) {
      return;
    }
    if (connectionState !== 'connected') {
      throw new Error('Соединение в реальном времени недоступно');
    }

    setIsSending(true);
    setChatErrorMessage(null);
    try {
      const uploadedFiles: Array<{ file_id: number; upload_token: string }> = [];
      for (const file of params.files) {
        const uploaded = await uploadOfferMessageFile(params.offerId, file);
        uploadedFiles.push({ file_id: uploaded.file_id, upload_token: uploaded.upload_token });
      }

      await realtimeClient.sendMessage(
        params.offerId,
        params.text,
        uploadedFiles
      );
      if (ownTypingActiveRef.current) {
        ownTypingActiveRef.current = false;
        await realtimeClient.typingStop(params.offerId);
      }
    } catch (error) {
      setChatErrorMessage(getErrorMessage(error, 'Не удалось отправить сообщение'));
      throw error;
    } finally {
      setIsSending(false);
    }
  }, [connectionState, realtimeClient]);

  const markReadByInputFocus = useCallback(async (params: {
    offerId: number;
    canSetReadMessages: boolean;
    canSetReceivedMessages: boolean;
    sessionLogin?: string;
    offerItems: typeof offerItems;
  }) => {
    if (!params.canSetReadMessages || !params.sessionLogin || messages.length === 0) {
      return;
    }

    const incomingMessages = messages.filter((item: OfferWorkspaceMessage) => item.offer_id === params.offerId && item.user_id !== params.sessionLogin);
    const lastIncomingMessage = incomingMessages[incomingMessages.length - 1];
    if (!lastIncomingMessage) {
      return;
    }

    try {
      if (connectionState === 'connected') {
        await realtimeClient.markRead(params.offerId, {});
      } else {
        const incomingSendIds = incomingMessages.filter((item: OfferWorkspaceMessage) => item.status === 'send').map((item: OfferWorkspaceMessage) => item.id);
        if (params.canSetReceivedMessages && incomingSendIds.length > 0) {
          await markOfferMessagesReceived(params.offerId, incomingSendIds);
        }
        await markOfferMessagesRead(params.offerId);
        await loadMessages(params.offerId, params.offerItems, false);
      }
    } catch (error) {
      setChatErrorMessage(getErrorMessage(error, 'Не удалось обновить статус прочтения сообщений'));
    }
  }, [connectionState, loadMessages, messages, realtimeClient]);

  const handleDraftActivity = useCallback(async (params: {
    offerId: number;
    text: string;
    canSendMessage: boolean;
  }) => {
    if (!params.canSendMessage || connectionState !== 'connected') {
      return;
    }

    const hasText = params.text.trim().length > 0;
    if (hasText && !ownTypingActiveRef.current) {
      ownTypingActiveRef.current = true;
      void realtimeClient.typingStart(params.offerId).catch(() => undefined);
    }

    if (typingStopTimerRef.current !== null) {
      window.clearTimeout(typingStopTimerRef.current);
      typingStopTimerRef.current = null;
    }

    if (!hasText) {
      if (ownTypingActiveRef.current) {
        ownTypingActiveRef.current = false;
        void realtimeClient.typingStop(params.offerId).catch(() => undefined);
      }
      return;
    }

    typingStopTimerRef.current = window.setTimeout(() => {
      if (!ownTypingActiveRef.current) {
        return;
      }
      ownTypingActiveRef.current = false;
      void realtimeClient.typingStop(params.offerId).catch(() => undefined);
    }, TYPING_STOP_DELAY_MS);
  }, [connectionState, realtimeClient]);

  return {
    messages,
    chatActions,
    isSending,
    chatErrorMessage,
    typingUserIds,
    loadMessages,
    handleSendMessage,
    markReadByInputFocus,
    handleDraftActivity,
    setChatErrorMessage
  };
};
