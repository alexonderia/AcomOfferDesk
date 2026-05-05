import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Box,
  Button,
  Stack,
  TextField,
  Typography
} from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';
import { getContractorRequestView } from '@shared/api/requests/getContractorRequestView';
import type { ContractorRequestView } from '@shared/api/requests/getContractorRequestView';
import { createOfferForRequest } from '@shared/api/offers/createOfferForRequest';
import { downloadFile } from '@shared/api/fileDownload';
import { RequestDetailsMainCard } from '@features/request-details/ui/RequestDetailsMainCard';
import type { RequestStatus } from '@features/request-details/model/requestDetailsUtils';

const statusOptions = [
  { value: 'open', label: 'Открыта', color: '#2e7d32' },
  { value: 'review', label: 'На рассмотрении', color: '#ed6c02' },
  { value: 'closed', label: 'Закрыта', color: '#787878ff' },
  { value: 'cancelled', label: 'Отменена', color: '#d32f2f' }
] as const;

const toRequestStatus = (status: string | null | undefined): RequestStatus => {
  if (status === 'review' || status === 'closed' || status === 'cancelled') {
    return status;
  }
  return 'open';
};

const parseAmountInput = (value: string) => {
  const normalized = value.trim().replace(',', '.');
  if (!normalized) {
    return null;
  }

  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : Number.NaN;
};

export const ContractorRequestDetailsPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const requestId = Number(id ?? 0);
  const [request, setRequest] = useState<ContractorRequestView | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isResponding, setIsResponding] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [offerAmount, setOfferAmount] = useState('');
  const descriptionTextRef = useRef<HTMLParagraphElement | null>(null);

  useEffect(() => {
    if (!Number.isFinite(requestId) || requestId <= 0) {
      return;
    }

    let isMounted = true;
    setIsLoading(true);
    setErrorMessage(null);

    getContractorRequestView(requestId)
      .then((response) => {
        if (!isMounted) {
          return;
        }
        if (response.existing_offer?.actions.open_workspace) {
          navigate(`/offers/${response.existing_offer.offer_id}/workspace`, { replace: true });
          return;
        }
        setRequest(response);
      })
      .catch((error) => {
        if (isMounted) {
          setErrorMessage(error instanceof Error ? error.message : 'Ошибка загрузки заявки');
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [navigate, requestId]);

  const statusConfig = useMemo(
    () => statusOptions.find((item) => item.value === request?.status) ?? statusOptions[0],
    [request?.status]
  );

  const canCreateOffer = useMemo(
    () => Boolean(request?.actions.create_offer),
    [request?.actions.create_offer]
  );
  const requestStatus = toRequestStatus(request?.status);

  const handleRespond = async () => {
    if (!request) {
      return;
    }

    const parsedOfferAmount = parseAmountInput(offerAmount);
    if (Number.isNaN(parsedOfferAmount)) {
      setErrorMessage('Укажите корректную сумму КП');
      return;
    }
    if (parsedOfferAmount !== null && parsedOfferAmount < 0) {
      setErrorMessage('Сумма КП не может быть отрицательной');
      return;
    }

    setIsResponding(true);
    setErrorMessage(null);
    try {
      const createdOffer = await createOfferForRequest(
        request.id,
        undefined,
        parsedOfferAmount === null ? undefined : { offer_amount: parsedOfferAmount }
      );
      navigate(createdOffer.workspacePath);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Не удалось отправить отклик');
    } finally {
      setIsResponding(false);
    }
  };

  if (isLoading) {
    return <Typography>Загрузка...</Typography>;
  }

  if (!request) {
    if (errorMessage) {
      return (
        <Stack spacing={2} alignItems="flex-start">
          <Typography color="error">{errorMessage}</Typography>
        </Stack>
      );
    }
    return (
      <Stack spacing={2} alignItems="flex-start">
        <Typography color="text.secondary">Заявка не найдена.</Typography>
      </Stack>
    );
  }

  return (
    <Box>
      {errorMessage ? (
        <Typography color="error" sx={{ mb: 2 }}>
          {errorMessage}
        </Typography>
      ) : null}

      <RequestDetailsMainCard
        requestId={request.id}
        status={requestStatus}
        statusOptions={statusOptions}
        statusColor={statusConfig.color}
        canEditRequest={false}
        isEditMode={false}
        onStatusChange={() => undefined}
        descriptionText={request.description ?? ''}
        descriptionTextRef={descriptionTextRef}
        canExpandDescription={false}
        isDescriptionExpanded={false}
        onToggleDescription={() => undefined}
        ownerField={
          <TextField
            size="small"
            value={request.owner_full_name ?? request.owner_user_id ?? '-'}
            fullWidth
            InputProps={{ readOnly: true }}
          />
        }
        existingFiles={request.files}
        canDeleteRequestFiles={false}
        onDownloadFile={(downloadUrl, fileName) => void downloadFile(downloadUrl, fileName)}
        onRemoveExistingFile={() => undefined}
        newFile={null}
        onClearNewFile={() => undefined}
        canUploadRequestFiles={false}
        onNewFileSelected={() => undefined}
        canViewRequestAmounts={false}
        deadline={request.deadline_at ?? ''}
        initialAmount=""
        finalAmount=""
        onDeadlineChange={() => undefined}
        onInitialAmountChange={() => undefined}
        onFinalAmountChange={() => undefined}
        requestCreatedAt={null}
        requestClosedAt={null}
        requestDeadlineAt={request.deadline_at ?? null}
        requestOfferId="-"
        showOfferId={false}
        requestUpdatedAt={request.updated_at ?? null}
        hideUpdatedAtIfEmpty
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

      {canCreateOffer ? (
        <Box
          sx={(theme) => ({
            mt: 2,
            width: 'fit-content',
            maxWidth: '100%',
            border: `1px solid ${theme.palette.divider}`,
            borderRadius: `${theme.acomShape.panelRadius}px`,
            backgroundColor: theme.palette.background.paper,
            p: { xs: 1.5, sm: 2 }
          })}
        >
          <Stack spacing={0.9} sx={{ width: 'fit-content', maxWidth: { xs: '100%', sm: 360 } }}>
            <TextField
              size="small"
              value={offerAmount}
              onChange={(event) => setOfferAmount(event.target.value)}
              inputProps={{ min: 0, step: '0.01', inputMode: 'decimal' }}
              placeholder="Сумма КП, руб."
              sx={{ width: { xs: '100%', sm: 180 } }}
            />
            <Typography variant="caption" color="text.secondary" sx={{ maxWidth: 280, lineHeight: 1.3 }}>
              Можно заполнить после создания отклика.
            </Typography>
            <Button
              variant="contained"
              disabled={isResponding}
              onClick={() => void handleRespond()}
              sx={{ width: { xs: '100%', sm: 'fit-content' }, minWidth: 150, py: 0.75 }}
            >
              {isResponding ? 'Создаём отклик...' : 'Откликнуться'}
            </Button>
          </Stack>
        </Box>
      ) : null}
    </Box>
  );
};
