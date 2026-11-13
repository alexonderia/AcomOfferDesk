import { useEffect, useRef, useState } from 'react';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import {
  Box,
  Button,
  Chip,
  IconButton,
  Paper,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { useMediaQuery } from '@mui/material';
import { useIsMobileViewport } from '@shared/lib/responsive';
import { formatDate, formatAmount } from '@shared/lib/formatters';
import { getFileKey } from '@shared/lib/files';
import { downloadFile } from '@shared/api/fileDownload';
import { FilePreviewTrigger } from '@shared/components/file-preview/FilePreviewTrigger';
import { useSystemToasts } from '@shared/ui/toasts';
import { OfferWorkspaceChatPanel } from './OfferWorkspaceChatPanel';
import { OFFER_WORKSPACE_CHAT_WIDTH_PX, OfferWorkspaceChatDock } from './OfferWorkspaceChatDock';
import { useOfferWorkspace } from '../model/useOfferWorkspace';
import { RequestDetailsMainCard } from '@features/request-details/ui/RequestDetailsMainCard';
import { statusOptions, type RequestStatus } from '@features/request-details/model/requestDetailsUtils';
import { ContractorLoginAccessBadge } from '@features/contractors/components/ContractorLoginAccessBadge';
import { ContractorStatusPill } from '@features/contractors/components/contractorUi';
import { StatusPill, type StatusPillTone } from '@shared/ui/StatusPill';
import { themeTokens } from '@shared/theme/tokens';

const offerDecisionOptions = [
  { value: 'accepted', label: 'Принято' },
  { value: 'rejected', label: 'Отказано' }
] as const;


const workspaceControlSx = {
  height: themeTokens.button.minHeight,
  minHeight: themeTokens.button.minHeight,
  borderRadius: `${themeTokens.shape.buttonRadius}px`,
  fontSize: themeTokens.typography.body2FontSize,
} as const;

const offerStatusTone: Record<string, StatusPillTone> = {
  submitted: 'warning', accepted: 'success', rejected: 'neutral', deleted: 'error',
};

const getOfferStatusLabel = (status: string | null) => {
  if (status === 'accepted') {
    return 'Принято';
  }

  if (status === 'submitted') {
    return 'На рассмотрении';
  }

  if (status === 'deleted') {
    return 'Удалено';
  }

  if (status === 'rejected') {
    return 'Отказано';
  }

  return 'Неизвестный статус';
};

export const OfferWorkspaceView = () => {
  const theme = useTheme();
  const isDesktopWithSidebar = useMediaQuery(theme.breakpoints.up('lg'));
  const isMobileViewport = useIsMobileViewport();
  const { showErrorToast, showSystemToast } = useSystemToasts();
  const descriptionTextRef = useRef<HTMLParagraphElement | null>(null);
  const lastShownErrorRef = useRef<string | null>(null);
  const lastShownSaveSuccessRef = useRef<number | null>(null);
  const [isOfferEditMode, setIsOfferEditMode] = useState(false);
  const {
    session,
    workspace,
    contractorInfo,
    contractorLoginAccess,
    isContractorAccessLoading,
    selectedOffer,
    sortedOffers,
    setSelectedOfferId,
    fileInputRef,
    isLoading,
    isUploading,
    errorMessage,
    isChatOpen,
    setIsChatOpen,
    offerDecisionStatus,
    isUpdatingOfferStatus,
    isUpdatingOfferAmount,
    lastOfferSaveSuccessAt,
    messages,
    typingUserIds,
    isSending,
    canUpload,
    canDeleteFile,
    canSendMessage,
    canViewMessages,
    retryChat,
    canSendMessageWithAttachments,
    canSetReadMessages,
    canSetReceivedMessages,
    canEditOfferStatus,
    canEditOfferAmount,
    canDeleteOffer,
    isContractor,
    acceptedOfferId,
    offerAmountInput,
    setOfferAmountInput,
    baselineOfferAmount,
    existingOfferFiles = [],
    deletedOfferFileIds = [],
    newOfferFiles = [],
    setNewOfferFiles,
    handleCancelOfferEditing,
    handleUpload,
    handleDeleteFile,
    handleStatusChange,
    handleOfferAmountSave,
    handleDeleteOffer,
    handleCreateNewOffer,
    onSendMessage,
    onMessageInputClick,
    onMessageDraftChange
  } = useOfferWorkspace();

  const canViewRequestAmounts = Boolean(workspace?.request.actions.view_amounts);
  const canViewContractorInfo = Boolean(selectedOffer?.actions.view_contractor_info);
  const contractorStatus = contractorInfo?.status ?? workspace?.profile?.status;
  const accessState = contractorLoginAccess?.state;
  const hasEquivalentAccessStatus = (contractorStatus === 'active' && accessState === 'available')
    || (['inactive', 'blacklist'].includes(contractorStatus ?? '') && accessState === 'blocked')
    || (contractorStatus === 'review' && accessState === 'pending');
  const showLoginAccess = isContractorAccessLoading || !hasEquivalentAccessStatus;
  const hasOfferUpdatePermission = Boolean(session?.permissions.includes('offers.update'));
  const hasDepartmentOfferUpdateDelegation = Boolean(session?.permissions.includes('department.offers.update'));
  const requestStatus = (workspace?.request.status ?? 'open') as RequestStatus;
  const canModifyOffer = requestStatus !== 'closed' && requestStatus !== 'cancelled';
  const canEnterOfferEditMode = canModifyOffer && (
    canDeleteOffer
    || ((hasDepartmentOfferUpdateDelegation || hasOfferUpdatePermission)
      && (canEditOfferAmount || canUpload || canDeleteFile))
  );
  const canEditOfferDecision = canModifyOffer && canEditOfferStatus;
  const normalizedErrorMessage = (errorMessage ?? '').toLowerCase();
  const isChatAccessError = normalizedErrorMessage.includes('просмотра чата') || normalizedErrorMessage.includes('доступ') && normalizedErrorMessage.includes('чат');
  const visibleErrorMessage = !canViewMessages && isChatAccessError ? null : errorMessage;

  const canCreateNewOffer = Boolean(workspace?.request.actions.create_offer);

  const statusTone = requestStatus === 'open'
    ? 'success'
    : requestStatus === 'review'
      ? 'warning'
      : 'neutral';
  const statusColor = statusTone === 'success'
    ? theme.palette.success.main
    : statusTone === 'warning'
      ? theme.palette.warning.main
      : theme.palette.text.secondary;

  useEffect(() => {
    const chatOffset = isDesktopWithSidebar && isChatOpen ? `${OFFER_WORKSPACE_CHAT_WIDTH_PX}px` : '0px';
    document.documentElement.style.setProperty('--offer-workspace-chat-offset', chatOffset);

    return () => {
      document.documentElement.style.setProperty('--offer-workspace-chat-offset', '0px');
    };
  }, [isChatOpen, isDesktopWithSidebar]);

  useEffect(() => {
    setIsOfferEditMode(false);
  }, [selectedOffer?.offer_id]);

  useEffect(() => {
    if (!canViewMessages && isChatOpen) {
      setIsChatOpen(false);
    }
  }, [canViewMessages, isChatOpen, setIsChatOpen]);

  useEffect(() => {
    if (isOfferEditMode && !canEnterOfferEditMode) {
      setIsOfferEditMode(false);
    }
  }, [canEnterOfferEditMode, isOfferEditMode]);

  useEffect(() => {
    if (!visibleErrorMessage) {
      lastShownErrorRef.current = null;
      return;
    }

    if (lastShownErrorRef.current === visibleErrorMessage) {
      return;
    }

    showErrorToast(visibleErrorMessage);
    lastShownErrorRef.current = visibleErrorMessage;
  }, [showErrorToast, visibleErrorMessage]);

  useEffect(() => {
    if (!lastOfferSaveSuccessAt) {
      return;
    }
    if (lastShownSaveSuccessRef.current === lastOfferSaveSuccessAt) {
      return;
    }

    showSystemToast({
      severity: 'success',
      message: 'Изменения КП успешно сохранены.',
    });
    lastShownSaveSuccessRef.current = lastOfferSaveSuccessAt;
  }, [lastOfferSaveSuccessAt, showSystemToast]);

  if (isLoading) {
    return <Typography>Загрузка...</Typography>;
  }

  if (!workspace || !selectedOffer) {
    return <Typography color="text.secondary">Рабочее пространство КП недоступно.</Typography>;
  }

  return (
    <Stack
      direction={{ xs: 'column', lg: 'row' }}
      sx={{
        height: '100%',
        minHeight: 0,
        alignItems: 'stretch',
        overflow: 'visible',
        minWidth: 0
      }}
    >
      <Box
        sx={{
          flex: 1,
          minWidth: 0,
          width: { lg: isChatOpen ? `calc(100% - ${OFFER_WORKSPACE_CHAT_WIDTH_PX}px)` : '100%' },
          maxWidth: { lg: isChatOpen ? `calc(100% - ${OFFER_WORKSPACE_CHAT_WIDTH_PX}px)` : '100%' },
          p: 0,
          pr: 0,
          overflowY: { xs: 'visible', lg: 'auto' },
          scrollbarWidth: 'none',
          '&::-webkit-scrollbar': {
            display: 'none'
          }
        }}
      >

        <RequestDetailsMainCard
          requestId={workspace.request.request_id}
          status={requestStatus}
          statusOptions={statusOptions}
          statusColor={statusColor}
          canEditRequest={false}
          isEditMode={false}
          onStatusChange={() => undefined}
          descriptionText={workspace.request.description ?? ''}
          descriptionTextRef={descriptionTextRef}
          canExpandDescription={false}
          isDescriptionExpanded={false}
          onToggleDescription={() => undefined}
          ownerField={
            <TextField
              size="small"
              value={workspace.request.owner_full_name ?? '-'}
              fullWidth
              InputProps={{ readOnly: true }}
            />
          }
          responsibleContact={{
            fullName: workspace.request.owner_full_name ?? workspace.request.owner_user_id ?? null,
            phone: workspace.request.owner_phone ?? null,
            mail: workspace.request.owner_mail ?? null
          }}
          existingFiles={workspace.request.files}
          canDeleteRequestFiles={false}
          onDownloadFile={(downloadUrl, fileName) => {
            return downloadFile(downloadUrl, fileName);
          }}
          onRemoveExistingFile={() => undefined}
          newFiles={[]}
          onRemoveNewFile={() => undefined}
          canUploadRequestFiles={false}
          onNewFilesAdded={() => undefined}
          canViewRequestAmounts={canViewRequestAmounts}
          deadline=""
          initialAmount={formatAmount(workspace.request.initial_amount ?? null)}
          finalAmount={formatAmount(workspace.request.final_amount ?? null)}
          onDeadlineChange={() => undefined}
          onInitialAmountChange={() => undefined}
          onFinalAmountChange={() => undefined}
          requestCreatedAt={workspace.request.created_at ?? null}
          requestClosedAt={workspace.request.closed_at ?? null}
          requestDeadlineAt={workspace.request.deadline_at ?? null}
          requestOfferId={workspace.request.id_offer ?? workspace.request.chosen_offer_id ?? '-'}
          showOfferId={false}
          requestUpdatedAt={workspace.request.updated_at ?? null}
          isSaving={false}
          canSaveRequestChanges={false}
          hasPendingChanges={false}
          hasValidationError={false}
          canEnterEditMode={false}
          onCancelEditing={() => undefined}
          onSave={() => undefined}
          onStartEdit={() => undefined}
          hideActions
        />

        {canViewContractorInfo ? (
        <Paper
          sx={(themeValue) => ({
            mt: 2.5,
            px: { xs: 2, md: 3 },
            py: { xs: 2, md: 2.5 },
            borderRadius: `${themeValue.acomShape.panelRadius}px`,
            border: `1px solid ${themeValue.palette.divider}`
          })}
        >
          <Typography variant="h6" sx={{ mb: 1 }}>
            Информация о контрагенте
          </Typography>
          <Stack direction="row" alignItems="center" gap={1} flexWrap="wrap" sx={{ mb: 1.5 }}>
            {contractorStatus ? <ContractorStatusPill value={contractorStatus} /> : null}
            {showLoginAccess ? <ContractorLoginAccessBadge access={contractorLoginAccess}
              loading={isContractorAccessLoading} iconOnly={Boolean(contractorStatus)} /> : null}
          </Stack>
          <Box sx={{ display: 'grid', gap: 1.5, alignItems: 'stretch',
            gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 260px), 1fr))' }}>
            <Paper
              variant="outlined"
              sx={{
                p: 1.5,
                minWidth: 0
              }}
            >
              <Stack spacing={0.75}>
                <Stack direction="row" justifyContent="space-between" spacing={1} alignItems="center">
                  <Typography variant="body2" color="text.secondary">ИНН</Typography>
                  <Typography variant="body2" sx={{ textAlign: 'right', overflowWrap: 'anywhere' }}>{contractorInfo?.inn ?? workspace.company_contacts?.inn ?? '-'}</Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between" spacing={1} alignItems="center">
                  <Typography variant="body2" color="text.secondary">Компания</Typography>
                  <Typography variant="body2" sx={{ textAlign: 'right', overflowWrap: 'anywhere' }}>{contractorInfo?.company_name ?? workspace.company_contacts?.company_name ?? '-'}</Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between" spacing={1} alignItems="center">
                  <Typography variant="body2" color="text.secondary">Телефон</Typography>
                  <Typography variant="body2" sx={{ textAlign: 'right', overflowWrap: 'anywhere' }}>{contractorInfo?.company_phone ?? workspace.company_contacts?.phone ?? '-'}</Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between" spacing={1} alignItems="center">
                  <Typography variant="body2" color="text.secondary">E-mail</Typography>
                  <Typography variant="body2" sx={{ textAlign: 'right', overflowWrap: 'anywhere' }}>
                    {contractorInfo?.company_mail ?? workspace.company_contacts?.mail ?? '-'}
                  </Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between" spacing={1} alignItems="center">
                  <Typography variant="body2" color="text.secondary">Адрес</Typography>
                  <Typography variant="body2" sx={{ textAlign: 'right', overflowWrap: 'anywhere' }}>{contractorInfo?.address ?? workspace.company_contacts?.address ?? '-'}</Typography>
                </Stack>
              </Stack>
            </Paper>
            <Paper
              variant="outlined"
              sx={{
                p: 1.5,
                minWidth: 0
              }}
            >
              <Stack spacing={0.5}>
                <Typography variant="body2" color="text.secondary">Дополнительная информация</Typography>
                <Typography variant="body2">
                  {contractorInfo?.note ?? workspace.company_contacts?.note ?? '-'}
                </Typography>
              </Stack>
            </Paper>
            <Paper
              variant="outlined"
              sx={{
                p: 1.5,
                minWidth: 0
              }}
            >
              <Stack spacing={0.75}>
                <Stack direction="row" justifyContent="space-between" spacing={1} alignItems="center">
                  <Typography variant="body2" color="text.secondary">ФИО</Typography>
                  <Typography variant="body2" sx={{ textAlign: 'right', overflowWrap: 'anywhere' }}>
                    {contractorInfo?.full_name ?? workspace.profile?.full_name ?? '-'}
                  </Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between" spacing={1} alignItems="center">
                  <Typography variant="body2" color="text.secondary">Телефон</Typography>
                  <Typography variant="body2" sx={{ textAlign: 'right', overflowWrap: 'anywhere' }}>
                    {contractorInfo?.phone ?? workspace.profile?.phone ?? '-'}
                  </Typography>
                </Stack>
                <Stack direction="row" justifyContent="space-between" spacing={1} alignItems="center">
                  <Typography variant="body2" color="text.secondary">E-mail</Typography>
                  <Typography variant="body2" sx={{ textAlign: 'right', overflowWrap: 'anywhere' }}>
                    {contractorInfo?.mail ?? workspace.profile?.mail ?? '-'}
                  </Typography>
                </Stack>
              </Stack>
            </Paper>
          </Box>
        </Paper>
        ) : null}

        {isContractor && canCreateNewOffer ? (
          <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent={{ xs: 'stretch', sm: 'flex-end' }} sx={{ mt: 2.5 }}>
            <Button
              variant="contained"
              disabled={isUpdatingOfferStatus}
              onClick={() => void handleCreateNewOffer()}
              sx={{ width: { xs: '100%', sm: 'auto' } }}
            >
              Новый отклик
            </Button>
          </Stack>
        ) : null}

        {sortedOffers.map((offerItem) => {
          const isCurrent = offerItem.offer_id === selectedOffer.offer_id;
          const isCurrentInEditMode = isCurrent && isOfferEditMode && canEnterOfferEditMode;
          const hasOfferAmountChanges = offerAmountInput !== baselineOfferAmount && offerAmountInput.trim().length > 0;
          const hasOfferFileChanges = deletedOfferFileIds.length > 0 || newOfferFiles.length > 0;
          const canSaveOfferChanges = hasOfferAmountChanges || hasOfferFileChanges;
          const offerStatusLabel = getOfferStatusLabel(offerItem.status ?? null);
          const filesToRender = isCurrent ? existingOfferFiles : offerItem.files;
          return (
            <Paper
              key={offerItem.offer_id}
              sx={(themeValue) => ({
                mt: 2.5,
                px: { xs: 2, md: 3 },
                py: { xs: 2, md: 2.5 },
                borderRadius: `${themeValue.acomShape.panelRadius}px`,
                border: `1px solid ${themeValue.palette.divider}`,
                backgroundColor: themeValue.palette.background.paper
              })}
            >
              <Stack
                direction={{ xs: 'column', lg: 'row' }}
                alignItems={{ xs: 'flex-start', lg: 'center' }}
                justifyContent="space-between"
                spacing={1.5}
                useFlexGap
                flexWrap="wrap"
                sx={{ mb: 1.5 }}
              >
                <Stack direction="row" spacing={1.2} alignItems="center" useFlexGap flexWrap="wrap">
                  <Typography variant="h5" sx={{ fontWeight: 700 }}>
                    КП №{offerItem.offer_id}
                  </Typography>
                  <StatusPill label={offerStatusLabel} tone={offerStatusTone[offerItem.status] ?? 'neutral'} />
                </Stack>

                <Stack direction="row" spacing={1} alignItems="center" useFlexGap flexWrap="wrap">
                  {isCurrentInEditMode && canDeleteOffer ? (
                    <Button
                      variant="contained"
                      startIcon={<DeleteOutlineIcon />}
                      onClick={() => void handleDeleteOffer()}
                      disabled={isUpdatingOfferStatus || offerItem.status === 'deleted'}
                      sx={(theme) => ({
                        ...workspaceControlSx,
                        backgroundColor: theme.palette.error.main,
                        color: theme.palette.error.contrastText,
                        boxShadow: 'none',
                        '&:hover': {
                          backgroundColor: theme.palette.error.dark,
                          boxShadow: 'none'
                        },
                        '&:disabled': {
                          backgroundColor: theme.palette.error.light,
                          color: theme.palette.error.contrastText
                        }
                      })}
                    >
                      {isContractor ? 'Удалить отклик' : 'Удалить КП'}
                    </Button>
                  ) : null}
                  {canEditOfferDecision && isCurrent ? (
                    <Select
                      size="small"
                      value={offerDecisionStatus}
                      displayEmpty
                      disabled={isUpdatingOfferStatus || offerItem.status === 'deleted'}
                      onChange={(event) => void handleStatusChange(event.target.value as 'accepted' | 'rejected' | '')}
                      sx={{
                        ...workspaceControlSx,
                        width: { xs: '100%', sm: 'auto' },
                        minWidth: { xs: '100%', sm: 230 },
                        '& .MuiOutlinedInput-input': { py: 1 }
                      }}
                    >
                      <MenuItem value="">
                        <Typography variant="body2" color="text.secondary">
                          Выберите статус
                        </Typography>
                      </MenuItem>
                      {offerDecisionOptions.map((option) => {
                        const isAcceptedBlocked = option.value === 'accepted' && Boolean(acceptedOfferId) && acceptedOfferId !== offerItem.offer_id;
                        return (
                          <MenuItem key={option.value} value={option.value} disabled={isAcceptedBlocked}>
                            {option.label}
                          </MenuItem>
                        );
                      })}
                    </Select>
                  ) : null}
                </Stack>
              </Stack>
              <Stack
                direction={{ xs: 'column', sm: 'row' }}
                spacing={1}
                sx={{ mt: 1.5, mb: 1.2 }}
              >
                <Box
                  sx={(themeValue) => ({
                    border: `1px solid ${themeValue.palette.divider}`,
                    borderRadius: `${themeValue.acomShape.controlRadius}px`,
                    backgroundColor: themeValue.palette.background.paper,
                    p: 1.2,
                    minWidth: { sm: 340 },
                    maxWidth: { sm: 380 },
                    display: 'grid',
                    gap: 0.8
                  })}
                >
                  <Stack
                    direction={{ xs: 'column', sm: 'row' }}
                    alignItems={{ xs: 'flex-start', sm: 'center' }}
                    justifyContent="space-between"
                    spacing={1}
                  >
                    <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
                      Создана
                    </Typography>
                    <Typography sx={{ fontWeight: 500, textAlign: { xs: 'left', sm: 'right' } }}>
                      {formatDate(offerItem.created_at)}
                    </Typography>
                  </Stack>
                  <Stack
                    direction={{ xs: 'column', sm: 'row' }}
                    alignItems={{ xs: 'flex-start', sm: 'center' }}
                    justifyContent="space-between"
                    spacing={1}
                  >
                    <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
                      Сумма КП, руб.
                    </Typography>
                    {isCurrent && canEditOfferAmount && isCurrentInEditMode ? (
                      <TextField
                        size="small"
                        value={offerAmountInput}
                        onChange={(event) => setOfferAmountInput(event.target.value)}
                        disabled={isUpdatingOfferAmount}
                        inputProps={{ min: 0, step: '0.01', inputMode: 'decimal', 'aria-label': 'Сумма КП, руб.' }}
                        sx={{ width: { xs: '100%', sm: 160 }, '& .MuiOutlinedInput-root': workspaceControlSx }}
                      />
                    ) : (
                      <Typography sx={{ fontWeight: 500, textAlign: { xs: 'left', sm: 'right' } }}>
                        {formatAmount(offerItem.offer_amount)}
                      </Typography>
                    )}
                  </Stack>
                </Box>
              </Stack>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 0.8 }}>
                Файлы КП
              </Typography>
              <Stack direction="row" flexWrap="wrap" useFlexGap gap={1}>
                {filesToRender.length === 0 ? (
                  <Typography color="text.secondary">Файлы КП не прикреплены.</Typography>
                ) : (
                  filesToRender.map((file) => (
                    <FilePreviewTrigger key={file.id} source={{ name: file.name, downloadUrl: file.download_url }}>
                      {(openPreview) => (
                        <Chip
                          label={file.name}
                          variant="outlined"
                          sx={{ borderRadius: 999, '& .MuiChip-label': { px: 1.2 } }}
                          onClick={openPreview}
                          onDelete={canDeleteFile && isCurrentInEditMode ? () => void handleDeleteFile(file.id) : undefined}
                        />
                      )}
                    </FilePreviewTrigger>
                  ))
                )}
                {isCurrentInEditMode
                  ? newOfferFiles.map((file) => (
                    <FilePreviewTrigger key={getFileKey(file)} source={{ name: file.name, file }}>
                      {(openPreview) => (
                        <Chip
                          label={file.name}
                          onClick={openPreview}
                          color="primary"
                          variant="outlined"
                          onDelete={() =>
                            setNewOfferFiles((prev) => prev.filter((item) => getFileKey(item) !== getFileKey(file)))}
                        />
                      )}
                    </FilePreviewTrigger>
                  ))
                  : null}
                {canUpload && isCurrentInEditMode ? (
                  <IconButton
                    size="small"
                    aria-label="Добавить файлы"
                    sx={{
                      alignSelf: 'center',
                      color: 'primary.main',
                      width: 32,
                      height: 32,
                      p: 0,
                      '&:hover': {
                        backgroundColor: 'transparent'
                      }
                    }}
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <AddCircleOutlineIcon sx={{ fontSize: 32 }} />
                  </IconButton>
                ) : null}
              </Stack>
              <Stack
                direction={{ xs: 'column', sm: 'row' }}
                alignItems={{ xs: 'stretch', sm: 'center' }}
                justifyContent="space-between"
                spacing={1}
                flexWrap="nowrap"
                sx={{ mt: 1.2 }}
              >
                <Typography variant="body2" color="text.secondary">Обновлено {formatDate(offerItem.updated_at, true)}</Typography>
                <Stack
                  direction="row"
                  spacing={1}
                  alignItems="center"
                  sx={{ justifyContent: 'flex-end', flexShrink: 0, '& > .MuiButton-root': workspaceControlSx }}
                >
                  {isCurrentInEditMode ? (
                    <Button
                      variant="outlined"
                      onClick={() => {
                        handleCancelOfferEditing();
                        setIsOfferEditMode(false);
                      }}
                      disabled={isUpdatingOfferAmount}
                    >
                      Отмена
                    </Button>
                  ) : (
                    isCurrent ? (
                      canEnterOfferEditMode ? (
                        <Button
                          variant="outlined"
                          startIcon={isMobileViewport ? undefined : <EditOutlinedIcon fontSize="small" />}
                          onClick={() => setIsOfferEditMode(true)}
                          disabled={isUpdatingOfferAmount}
                          aria-label="Изменить"
                          sx={{
                            ...workspaceControlSx,
                            minWidth: isMobileViewport ? themeTokens.button.minHeight : undefined,
                            width: isMobileViewport ? themeTokens.button.minHeight : 'auto',
                            px: isMobileViewport ? 0 : undefined
                          }}
                        >
                          {isMobileViewport ? <EditOutlinedIcon fontSize="small" /> : 'Изменить'}
                        </Button>
                      ) : null
                    ) : (
                      <Button
                        variant="outlined"
                        onClick={() => {
                          setSelectedOfferId(offerItem.offer_id);
                        }}
                        disabled={isUpdatingOfferAmount}
                      >
                        Открыть
                      </Button>
                    )
                  )}
                  {isCurrentInEditMode && (canEditOfferAmount || canUpload || canDeleteFile) ? (
                    <Button
                      variant={canSaveOfferChanges ? 'contained' : 'outlined'}
                      onClick={() => void handleOfferAmountSave()}
                      disabled={isUpdatingOfferAmount || isUploading || !canSaveOfferChanges}
                    >
                      {isUpdatingOfferAmount ? 'Сохранение...' : 'Сохранить'}
                    </Button>
                  ) : null}
                </Stack>
              </Stack>

              {isCurrent ? (
                <input
                  ref={fileInputRef}
                  type="file"
                  hidden
                  multiple
                  onChange={(event) => void handleUpload(event)}
                />
              ) : null}

            </Paper>
          );
        })}
      </Box>

      {canViewMessages ? (
        <OfferWorkspaceChatDock isOpen={isChatOpen} onOpen={() => setIsChatOpen(true)}>
          {visibleErrorMessage ? <Button onClick={() => void retryChat()}>Повторить загрузку чата</Button> : null}
          <OfferWorkspaceChatPanel
            offerId={selectedOffer.offer_id}
            readOnlyNotice={!canSendMessage && !canSendMessageWithAttachments && !canSetReadMessages && !canSetReceivedMessages ? '\u0414\u043b\u044f \u0432\u0430\u0441 \u0447\u0430\u0442 \u0434\u043e\u0441\u0442\u0443\u043f\u0435\u043d \u0442\u043e\u043b\u044c\u043a\u043e \u0434\u043b\u044f \u043f\u0440\u043e\u0441\u043c\u043e\u0442\u0440\u0430.' : null}
            isOpen
            onToggleOpen={setIsChatOpen}
            messages={messages}
            typingUserIds={typingUserIds}
            sessionLogin={session?.login}
            canSendMessage={canSendMessage}
            canSendMessageWithAttachments={canSendMessageWithAttachments}
            isSending={isSending}
            onSendMessage={onSendMessage}
            onMessageInputClick={onMessageInputClick}
            onMessageDraftChange={onMessageDraftChange}
            onDownloadAttachment={(downloadUrl, name) => {
              return downloadFile(downloadUrl, name);
            }}
            contractorUserId={selectedOffer.contractor_user_id}
            contractorLoginAccess={canViewContractorInfo && !isContractor ? contractorLoginAccess : undefined}
            isContractorAccessLoading={isContractorAccessLoading}
          />
        </OfferWorkspaceChatDock>
      ) : null}
    </Stack>
  );
};
