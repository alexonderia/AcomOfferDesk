import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { ChangeEvent } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '@app/providers/AuthProvider';
import { useChatRealtime } from '@app/providers/ChatRealtimeProvider';
import { getOfferWorkspace } from '@shared/api/offers/getOfferWorkspace';
import type { OfferWorkspace } from '@shared/api/offers/getOfferWorkspace';
import { getOfferContractorInfo } from '@shared/api/offers/getOfferContractorInfo';
import type { OfferContractorInfo } from '@shared/api/offers/getOfferContractorInfo';
import { createOfferForRequest } from '@shared/api/offers/createOfferForRequest';
import { deleteOfferFile, updateOfferAmount, uploadOfferFile } from '@shared/api/offers/offerWorkspaceActions';
import { updateOfferStatus } from '@shared/api/offers/updateOfferStatus';
import { ROLE } from '@shared/constants/roles';
import { getErrorMessage } from '@shared/lib/errors';
import { useOfferMessages } from './useOfferMessages';

const workspacePollIntervalMs = 7000;

const buildWorkspaceSignature = (workspace: OfferWorkspace | null) => {
  if (!workspace) {
    return '';
  }

  return JSON.stringify({
    request: {
      id: workspace.request.request_id,
      updated_at: workspace.request.updated_at,
      status: workspace.request.status,
      deadline_at: workspace.request.deadline_at,
      files: workspace.request.files.map((file) => [file.id, file.name])
    },
    current_offer: {
      id: workspace.offer.offer_id,
      status: workspace.offer.status,
      updated_at: workspace.offer.updated_at,
      amount: workspace.offer.offer_amount,
      files: workspace.offer.files.map((file) => [file.id, file.name])
    },
    offers: workspace.offers.map((offer) => ({
      id: offer.offer_id,
      status: offer.status,
      updated_at: offer.updated_at,
      amount: offer.offer_amount,
      files: offer.files.map((file) => [file.id, file.name])
    }))
  });
};

const buildContractorSignature = (contractor: OfferContractorInfo | null) => {
  if (!contractor) {
    return '';
  }

  return JSON.stringify({
    user_id: contractor.user_id,
    full_name: contractor.full_name,
    phone: contractor.phone,
    mail: contractor.mail,
    company_name: contractor.company_name,
    inn: contractor.inn,
    company_phone: contractor.company_phone,
    company_mail: contractor.company_mail,
    address: contractor.address,
    note: contractor.note
  });
};

const toAmountInputValue = (value: number | null | undefined) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '';
  }

  return String(value);
};

const parseAmountInput = (value: string) => {
  const normalized = value.trim().replace(',', '.');
  if (!normalized) {
    return null;
  }

  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : Number.NaN;
};

export const useOfferWorkspace = () => {
  const { id } = useParams<{ id: string }>();
  const { session, logout } = useAuth();
  const { client: realtimeClient, connectionState, onEvent } = useChatRealtime();
  const navigate = useNavigate();
  const offerId = Number(id ?? 0);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const contractorInfoRef = useRef<OfferContractorInfo | null>(null);
  const workspaceRef = useRef<OfferWorkspace | null>(null);
  const previousSelectedOfferIdRef = useRef<number | null>(null);

  const [workspace, setWorkspace] = useState<OfferWorkspace | null>(null);
  const [contractorInfo, setContractorInfo] = useState<OfferContractorInfo | null>(null);
  const [selectedOfferId, setSelectedOfferId] = useState<number>(offerId);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isUpdatingOfferStatus, setIsUpdatingOfferStatus] = useState(false);
  const [offerDecisionStatus, setOfferDecisionStatus] = useState<'accepted' | 'rejected' | ''>('');
  const [isUpdatingOfferAmount, setIsUpdatingOfferAmount] = useState(false);
  const [offerAmountInput, setOfferAmountInput] = useState('');
  const [baselineOfferAmount, setBaselineOfferAmount] = useState('');

  const sortedOffers = useMemo(
    () => [...(workspace?.offers ?? [])].sort((left, right) => new Date(right.created_at ?? 0).getTime() - new Date(left.created_at ?? 0).getTime()),
    [workspace?.offers]
  );
  const selectedOffer = useMemo(
    () => sortedOffers.find((item) => item.offer_id === selectedOfferId) ?? sortedOffers[0] ?? workspace?.offer ?? null,
    [selectedOfferId, sortedOffers, workspace?.offer]
  );

  const {
    messages,
    chatActions,
    isSending,
    chatErrorMessage,
    typingUserIds,
    loadMessages,
    handleSendMessage,
    markReadByInputFocus,
    handleDraftActivity
  } = useOfferMessages({
    activeOfferId: selectedOfferId,
    offerItems: workspace?.offers ?? [],
    sessionLogin: session?.login,
    connectionState,
    onRealtimeEvent: onEvent,
    realtimeClient
  });

  const refreshWorkspace = useCallback(async (targetOfferId: number) => {
    const nextWorkspace = await getOfferWorkspace(targetOfferId);
    if (buildWorkspaceSignature(workspaceRef.current) !== buildWorkspaceSignature(nextWorkspace)) {
      workspaceRef.current = nextWorkspace;
      setWorkspace(nextWorkspace);
    }
    setSelectedOfferId((prev: number) => {
      const nextSelectedOfferId = nextWorkspace.offers.some((item) => item.offer_id === prev)
        ? prev
        : nextWorkspace.offers[0]?.offer_id ?? targetOfferId;
      return prev === nextSelectedOfferId ? prev : nextSelectedOfferId;
    });

    const nextContractorId = nextWorkspace.offer.contractor_user_id;
    if (!nextContractorId) {
      if (contractorInfoRef.current !== null) {
        contractorInfoRef.current = null;
        setContractorInfo(null);
      }
      return nextWorkspace;
    }
    if (contractorInfoRef.current?.user_id === nextContractorId) {
      return nextWorkspace;
    }
    try {
      const nextContractorInfo = await getOfferContractorInfo(nextContractorId);
      if (buildContractorSignature(contractorInfoRef.current) !== buildContractorSignature(nextContractorInfo)) {
        contractorInfoRef.current = nextContractorInfo;
        setContractorInfo(nextContractorInfo);
      }
    } catch {
      if (contractorInfoRef.current !== null) {
        contractorInfoRef.current = null;
        setContractorInfo(null);
      }
    }

    return nextWorkspace;
  }, []);

  const loadWorkspace = useCallback(async () => {
    if (!Number.isFinite(offerId) || offerId <= 0) {
      return;
    }
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const workspaceResponse = await getOfferWorkspace(offerId);
      workspaceRef.current = workspaceResponse;
      setWorkspace(workspaceResponse);
      const initialOfferId = workspaceResponse.offers.find((item) => item.offer_id === offerId)?.offer_id ?? workspaceResponse.offers[0]?.offer_id ?? offerId;
      setSelectedOfferId(initialOfferId);
      await loadMessages(initialOfferId, workspaceResponse.offers);

      if (workspaceResponse.offer.contractor_user_id) {
        try {
          const nextContractorInfo = await getOfferContractorInfo(workspaceResponse.offer.contractor_user_id);
          contractorInfoRef.current = nextContractorInfo;
          setContractorInfo(nextContractorInfo);
        } catch {
          contractorInfoRef.current = null;
          setContractorInfo(null);
        }
      }
    } catch (error) {
      setErrorMessage(getErrorMessage(error, 'Ошибка загрузки рабочего пространства КП'));
    } finally {
      setIsLoading(false);
    }
  }, [loadMessages, offerId]);

  useEffect(() => {
    contractorInfoRef.current = contractorInfo;
  }, [contractorInfo]);

  useEffect(() => {
    workspaceRef.current = workspace;
  }, [workspace]);

  useEffect(() => {
    const nextOfferAmount = toAmountInputValue(selectedOffer?.offer_amount ?? null);
    setOfferAmountInput(nextOfferAmount);
    setBaselineOfferAmount(nextOfferAmount);
  }, [selectedOffer?.offer_amount, selectedOffer?.offer_id]);

  useEffect(() => {
    void loadWorkspace();
  }, [loadWorkspace]);

  useEffect(() => {
    if (!selectedOfferId) {
      return;
    }

    const previousOfferId = previousSelectedOfferIdRef.current;
    if (previousOfferId && previousOfferId !== selectedOfferId) {
      realtimeClient.unsubscribe(previousOfferId);
      setErrorMessage(null);
    }

    realtimeClient.subscribe(selectedOfferId);
    previousSelectedOfferIdRef.current = selectedOfferId;

    return () => {
      realtimeClient.unsubscribe(selectedOfferId);
    };
  }, [realtimeClient, selectedOfferId]);

  useEffect(() => {
    if (!selectedOfferId) {
      return;
    }

    if (connectionState === 'connected') {
      return;
    }

    const interval = window.setInterval(() => {
      if (document.hidden) {
        return;
      }
      void refreshWorkspace(selectedOfferId)
        .then((nextWorkspace) => loadMessages(selectedOfferId, nextWorkspace.offers, false))
        .catch(() => undefined);
    }, workspacePollIntervalMs);
    return () => window.clearInterval(interval);
  }, [connectionState, loadMessages, refreshWorkspace, selectedOfferId]);

  const isContractor = session?.roleId === ROLE.CONTRACTOR;
  const isEconomist = session?.roleId === ROLE.SUPERADMIN || session?.roleId === ROLE.LEAD_ECONOMIST || session?.roleId === ROLE.PROJECT_MANAGER || session?.roleId === ROLE.ECONOMIST;
  const isSelectedOfferSubmitted = selectedOffer?.status === 'submitted';
  const canUpload = Boolean(selectedOffer?.actions.upload_file) && (!isContractor || isSelectedOfferSubmitted);
  const canDeleteFile = Boolean(selectedOffer?.actions.delete_file) && (!isContractor || isSelectedOfferSubmitted);
  const canSendMessage = chatActions.send_message;
  const canSendMessageWithAttachments = chatActions.attach_file || canSendMessage;
  const canSetReadMessages = chatActions.mark_messages_read;
  const canSetReceivedMessages = chatActions.mark_messages_received;
  const canEditOfferStatus = !isContractor && Boolean(selectedOffer && (selectedOffer.actions.accept || selectedOffer.actions.reject));
  const canEditOfferAmount = Boolean(selectedOffer?.actions.edit_amount);
  const canDeleteOwnOffer = isContractor && Boolean(selectedOffer?.actions.delete);

  const acceptedOfferId = sortedOffers.find((item) => item.status === 'accepted')?.offer_id ?? null;

  const handleUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file || !selectedOffer) return;
    setIsUploading(true);
    setErrorMessage(null);
    try {
      await uploadOfferFile(selectedOffer.offer_id, file);
      await refreshWorkspace(selectedOffer.offer_id);
    } catch (error) {
      setErrorMessage(getErrorMessage(error, 'Не удалось загрузить файл'));
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteFile = async (fileId: number) => {
    if (!selectedOffer) return;
    try {
      await deleteOfferFile(selectedOffer.offer_id, fileId);
      await refreshWorkspace(selectedOffer.offer_id);
    } catch (error) {
      setErrorMessage(getErrorMessage(error, 'Не удалось удалить файл'));
    }
  };

  const handleStatusChange = async (nextStatus: 'accepted' | 'rejected' | '') => {
    if (!selectedOffer || !nextStatus) return;
    if (nextStatus === 'accepted' && acceptedOfferId && acceptedOfferId !== selectedOffer.offer_id) {
      setErrorMessage('Нельзя одобрить более одного КП в рамках одной заявки');
      return;
    }
    const confirmed = window.confirm(nextStatus === 'accepted' ? 'Если принять это КП, остальные КП по заявке автоматически получат статус «Отказано». Продолжить?' : 'Вы уверены, что хотите изменить статус КП на «Отказано»?');
    if (!confirmed) return;
    setOfferDecisionStatus(nextStatus);
    setIsUpdatingOfferStatus(true);
    try {
      await updateOfferStatus({ offer_id: selectedOffer.offer_id, status: nextStatus });
      await refreshWorkspace(selectedOffer.offer_id);
    } catch (error) {
      setErrorMessage(getErrorMessage(error, 'Не удалось обновить статус КП'));
    } finally {
      setIsUpdatingOfferStatus(false);
    }
  };

  const handleDeleteOffer = async () => {
    if (!selectedOffer || selectedOffer.status === 'deleted') return;
    if (!window.confirm('Вы уверены, что хотите удалить отклик? После удаления отменить действие нельзя.')) return;
    setIsUpdatingOfferStatus(true);
    try {
      await updateOfferStatus({ offer_id: selectedOffer.offer_id, status: 'deleted' });
      await refreshWorkspace(selectedOffer.offer_id);
    } catch (error) {
      setErrorMessage(getErrorMessage(error, 'Не удалось удалить отклик'));
    } finally {
      setIsUpdatingOfferStatus(false);
    }
  };

  const handleOfferAmountSave = async () => {
    if (!selectedOffer || !canEditOfferAmount) return;

    const parsedOfferAmount = parseAmountInput(offerAmountInput);
    if (parsedOfferAmount === null) {
      setErrorMessage('Укажите сумму КП');
      return;
    }
    if (Number.isNaN(parsedOfferAmount)) {
      setErrorMessage('Укажите корректную сумму КП');
      return;
    }
    if (parsedOfferAmount < 0) {
      setErrorMessage('Сумма КП не может быть отрицательной');
      return;
    }

    setIsUpdatingOfferAmount(true);
    setErrorMessage(null);
    try {
      await updateOfferAmount(selectedOffer.offer_id, parsedOfferAmount);
      await refreshWorkspace(selectedOffer.offer_id);
    } catch (error) {
      setErrorMessage(getErrorMessage(error, 'Не удалось сохранить сумму КП'));
    } finally {
      setIsUpdatingOfferAmount(false);
    }
  };

  const handleCreateNewOffer = async () => {
    if (!workspace || !workspace.request.actions.create_offer) return;
    if (!window.confirm('Создать новый отклик для этой заявки? Предыдущие удалённые отклики останутся в истории.')) return;
    setIsUpdatingOfferStatus(true);
    try {
      const createdOffer = await createOfferForRequest(workspace.request.request_id);
      const refreshedWorkspace = await getOfferWorkspace(createdOffer.offerId);
      setWorkspace(refreshedWorkspace);
      setSelectedOfferId(createdOffer.offerId);
      await loadMessages(createdOffer.offerId, refreshedWorkspace.offers, false);
      navigate(createdOffer.workspacePath, { replace: true });
    } catch (error) {
      setErrorMessage(getErrorMessage(error, 'Не удалось создать новый отклик'));
    } finally {
      setIsUpdatingOfferStatus(false);
    }
  };

  return {
    session,
    logout,
    navigate,
    workspace,
    contractorInfo,
    selectedOffer,
    sortedOffers,
    selectedOfferId,
    setSelectedOfferId,
    fileInputRef,
    isLoading,
    isUploading,
    errorMessage: errorMessage ?? chatErrorMessage,
    isChatOpen,
    setIsChatOpen,
    offerDecisionStatus,
    isUpdatingOfferStatus,
    isUpdatingOfferAmount,
    messages,
    typingUserIds,
    connectionState,
    isSending,
    canUpload,
    canDeleteFile,
    canSendMessage,
    canSendMessageWithAttachments,
    canSetReadMessages,
    canSetReceivedMessages,
    canEditOfferStatus,
    canEditOfferAmount,
    canDeleteOwnOffer,
    isEconomist,
    isContractor,
    acceptedOfferId,
    offerAmountInput,
    setOfferAmountInput,
    baselineOfferAmount,
    handleUpload,
    handleDeleteFile,
    handleStatusChange,
    handleOfferAmountSave,
    handleDeleteOffer,
    handleCreateNewOffer,
    onSendMessage: async (text: string, files: File[]) => {
      if (!selectedOffer) return;
      await handleSendMessage({ offerId: selectedOffer.offer_id, text, files, canSendMessage });
    },
    onMessageInputClick: async () => {
      if (!selectedOffer || !workspace) return;
      await markReadByInputFocus({ offerId: selectedOffer.offer_id, canSetReadMessages, canSetReceivedMessages, sessionLogin: session?.login, offerItems: workspace.offers });
    },
    onMessageDraftChange: async (text: string) => {
      if (!selectedOffer) return;
      await handleDraftActivity({ offerId: selectedOffer.offer_id, text, canSendMessage });
    }
  };
};
