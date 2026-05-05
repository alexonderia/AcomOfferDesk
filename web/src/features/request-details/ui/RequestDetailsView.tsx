import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
    Alert,
    Box,
    Button,
    MenuItem,
    Select,
    Stack,
    TextField,
    Typography
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { OffersTable } from './OffersTable';
import type { OfferDecisionStatus, OfferStatusOption } from './OffersTable';
import { getRequestDetails } from '@shared/api/requests/getRequestDetails';
import type { RequestDetails, RequestDetailsFile, RequestDetailsOffer } from '@shared/api/requests/getRequestDetails';
import { getRequestEconomists } from '@shared/api/requests/getRequestEconomists';
import { sendRequestEmailNotifications } from '@shared/api/requests/sendRequestEmailNotifications';
import { markDeletedAlertViewed } from '@shared/api/offers/markDeletedAlertViewed';
import { updateOfferStatus } from '@shared/api/offers/updateOfferStatus';
import { deleteRequestFile, updateRequestDetails, uploadRequestFile } from '@shared/api/requests/updateRequestDetails';
import { getPlanOptions, type PlanOption } from '@shared/api/plans';
import { downloadFile } from '@shared/api/fileDownload';
import { AdditionalEmailsField, type AdditionalEmailsFieldHandle } from '@shared/components/AdditionalEmailsField';
import { UnavailableAwareMenuItem } from '@shared/components/UnavailableAwareMenuItem';
import { ToggleSection } from '@shared/components/ToggleSection';
import { formatUnavailabilityDate, type UnavailabilityPeriodInfo } from '@shared/lib/unavailability';
import { useRequestDetails } from '../model/useRequestDetails';
import {
    type RequestStatus,
    statusOptions,
    toDateInputValue,
    toAmountInputValue,
    parseAmountInput,
    normalizeOfferStatus,
    buildRequestDetailsSignature,
    toDeadlineIso,
} from '../model/requestDetailsUtils';
import { CreateManualOfferDialog } from './CreateManualOfferDialog';
import { RequestDetailsMainCard } from './RequestDetailsMainCard';

const offerStatusOptions: OfferStatusOption[] = [
    { value: 'accepted', label: 'Принято' },
    { value: 'rejected', label: 'Отказано' }
];

const requestStatusToneByValue: Record<RequestStatus, 'success' | 'warning' | 'neutral'> = {
    open: 'success',
    review: 'warning',
    closed: 'neutral',
    cancelled: 'neutral'
};

export const RequestDetailsView = () => {
    const { navigate, requestId } = useRequestDetails();
    const theme = useTheme();

    const [requestDetails, setRequestDetails] = useState<RequestDetails | null>(null);
    const [status, setStatus] = useState<RequestStatus>('open');
    const [baselineStatus, setBaselineStatus] = useState<RequestStatus>('open');
    const [deadline, setDeadline] = useState<string>('');
    const [baselineDeadline, setBaselineDeadline] = useState<string>('');
    const [ownerUserId, setOwnerUserId] = useState<string>('');
    const [baselineOwnerUserId, setBaselineOwnerUserId] = useState<string>('');
    const [initialAmount, setInitialAmount] = useState<string>('');
    const [baselineInitialAmount, setBaselineInitialAmount] = useState<string>('');
    const [finalAmount, setFinalAmount] = useState<string>('');
    const [baselineFinalAmount, setBaselineFinalAmount] = useState<string>('');
    const [planId, setPlanId] = useState<string>('');
    const [baselinePlanId, setBaselinePlanId] = useState<string>('');
    const [planOptions, setPlanOptions] = useState<PlanOption[]>([]);
    const [isPlanOptionsLoading, setIsPlanOptionsLoading] = useState(false);
    const [planOptionsOwnerId, setPlanOptionsOwnerId] = useState<string | null>(null);
    const [ownerOptions, setOwnerOptions] = useState<Array<{ id: string; label: string; unavailablePeriod: UnavailabilityPeriodInfo | null }>>([]);
    const [existingFiles, setExistingFiles] = useState<RequestDetailsFile[]>([]);
    const [deletedFileIds, setDeletedFileIds] = useState<number[]>([]);
    const [newFile, setNewFile] = useState<File | null>(null);
    const [isEditMode, setIsEditMode] = useState(false);
    const [isDescriptionExpanded, setIsDescriptionExpanded] = useState(false);
    const [isDescriptionOverflowing, setIsDescriptionOverflowing] = useState(false);
    const [additionalEmails, setAdditionalEmails] = useState<string[]>([]);
    const [additionalEmailsEnabled, setAdditionalEmailsEnabled] = useState(false);
    const additionalEmailsFieldRef = useRef<AdditionalEmailsFieldHandle | null>(null);
    const descriptionTextRef = useRef<HTMLParagraphElement | null>(null);
    const requestSignatureRef = useRef('');
    const hasPendingChangesRef = useRef(false);

    const [isSaving, setIsSaving] = useState(false);
    const [isSendingEmails, setIsSendingEmails] = useState(false);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [isClearingDeletedAlert, setIsClearingDeletedAlert] = useState(false);

    const [offers, setOffers] = useState<RequestDetailsOffer[]>([]);
    const [offersStatusMap, setOffersStatusMap] = useState<Record<number, OfferDecisionStatus>>({});
    const [offersLoading, setOffersLoading] = useState(false);
    const [offersError, setOffersError] = useState<string | null>(null);
    const [isManualOfferDialogOpen, setIsManualOfferDialogOpen] = useState(false);
    const pollIntervalMs = 10000;

    const hasDeletedAlert = (requestDetails?.count_deleted_alert ?? 0) > 0;
    const hasFileChanges = deletedFileIds.length > 0 || Boolean(newFile);
    const canViewRequestAmounts = useMemo(
        () => Boolean(requestDetails?.actions.view_amounts),
        [requestDetails?.actions.view_amounts]
    );
    const hasRequestFieldChanges =
        status !== baselineStatus ||
        deadline !== baselineDeadline ||
        (canViewRequestAmounts && initialAmount !== baselineInitialAmount) ||
        (canViewRequestAmounts && finalAmount !== baselineFinalAmount) ||
        planId !== baselinePlanId;
    const hasOwnerChange = ownerUserId !== baselineOwnerUserId;
    const hasPendingChanges = hasRequestFieldChanges || hasOwnerChange || hasFileChanges;

    useEffect(() => {
        hasPendingChangesRef.current = hasPendingChanges;
    }, [hasPendingChanges]);

    const canEditRequest = useMemo(() => Boolean(requestDetails?.actions.edit), [requestDetails?.actions.edit]);
    const canEditOwner = useMemo(
        () => Boolean(requestDetails?.actions.change_owner),
        [requestDetails?.actions.change_owner]
    );

    const canChangeOfferStatus = useMemo(
        () => (requestDetails?.offers ?? []).some((offer) => offer.actions.accept || offer.actions.reject),
        [requestDetails?.offers]
    );
    const canSendAdditionalEmails = useMemo(
        () => status === 'open' && Boolean(requestDetails?.actions.send_email_notifications),
        [requestDetails?.actions.send_email_notifications, status]
    );
    const isAdditionalEmailsFieldUnavailable = !canSendAdditionalEmails || isSendingEmails;
    const canUploadRequestFiles = useMemo(() => Boolean(requestDetails?.actions.upload_file), [requestDetails?.actions.upload_file]);
    const canDeleteRequestFiles = useMemo(() => Boolean(requestDetails?.actions.delete_file), [requestDetails?.actions.delete_file]);
    const canMarkDeletedAlertViewed = useMemo(
        () => Boolean(requestDetails?.actions.mark_deleted_alert_viewed),
        [requestDetails?.actions.mark_deleted_alert_viewed]
    );
    const canCreateManualOffer = useMemo(
        () => status === 'open' && Boolean(requestDetails?.actions.create_offer),
        [requestDetails?.actions.create_offer, status]
    );
    const canSaveRequestChanges =
        (hasRequestFieldChanges && canEditRequest)
        || (hasOwnerChange && canEditOwner)
        || (deletedFileIds.length > 0 && canDeleteRequestFiles)
        || (Boolean(newFile) && canUploadRequestFiles);
    const canEnterEditMode = canEditRequest || canEditOwner || canUploadRequestFiles || canDeleteRequestFiles;
    const statusTone = requestStatusToneByValue[status] ?? 'neutral';
    const statusColor = statusTone === 'success'
        ? theme.palette.success.main
        : statusTone === 'warning'
            ? theme.palette.warning.main
            : theme.palette.text.secondary;

    const todayDate = useMemo(() => {
        const now = new Date();
        const offsetMs = now.getTimezoneOffset() * 60000;
        return new Date(now.getTime() - offsetMs).toISOString().split('T')[0];
    }, []);

    const syncRequestState = useCallback((nextRequest: RequestDetails, forceBaseline: boolean) => {
        const nextSignature = buildRequestDetailsSignature(nextRequest);
        if (requestSignatureRef.current !== nextSignature) {
            requestSignatureRef.current = nextSignature;
            setRequestDetails(nextRequest);
            setOffers(nextRequest.offers ?? []);
            setOffersStatusMap(
                (nextRequest.offers ?? []).reduce<Record<number, OfferDecisionStatus>>((acc, offer) => {
                    acc[offer.offer_id] = normalizeOfferStatus(offer.status);
                    return acc;
                }, {})
            );
        }

        if (forceBaseline) {
            const nextStatus = (statusOptions.find((o) => o.value === nextRequest.status)?.value ?? 'open') as RequestStatus;
            const nextDeadline = toDateInputValue(nextRequest.deadline_at);
            const nextOwner = nextRequest.id_user ?? '';
            const nextInitialAmount = toAmountInputValue(nextRequest.initial_amount);
            const nextFinalAmount = toAmountInputValue(nextRequest.final_amount);
            const nextPlanId = nextRequest.id_plan ? String(nextRequest.id_plan) : '';
            setStatus(nextStatus);
            setBaselineStatus(nextStatus);
            setDeadline(nextDeadline);
            setBaselineDeadline(nextDeadline);
            setOwnerUserId(nextOwner);
            setBaselineOwnerUserId(nextOwner);
            setInitialAmount(nextInitialAmount);
            setBaselineInitialAmount(nextInitialAmount);
            setFinalAmount(nextFinalAmount);
            setBaselineFinalAmount(nextFinalAmount);
            setPlanId(nextPlanId);
            setBaselinePlanId(nextPlanId);
            setExistingFiles(nextRequest.files ?? []);
        }
    }, []);

    const fetchRequest = useCallback(
        async (showLoading: boolean) => {
            if (!Number.isFinite(requestId) || requestId <= 0) {
                return;
            }
            if (showLoading) {
                setOffersLoading(true);
            }
            try {
                const nextRequest = await getRequestDetails(requestId);
                syncRequestState(nextRequest, !hasPendingChangesRef.current);
                setOffersError(null);
            } catch (error) {
                setOffersError(error instanceof Error ? error.message : 'Не удалось загрузить заявку');
            } finally {
                if (showLoading) {
                    setOffersLoading(false);
                }
            }
        },
        [requestId, syncRequestState]
    );

    const fetchOwners = useCallback(async () => {
        if (!canEditOwner) {
            setOwnerOptions([]);
            return;
        }

        try {
            const economists = await getRequestEconomists();
            setOwnerOptions(
                economists.map((item) => ({
                    id: item.user_id,
                    label: `${item.full_name?.trim() || item.user_id} (${item.role})`,
                    unavailablePeriod: item.unavailable_period
                        ? {
                            status: item.unavailable_period.status,
                            startedAt: item.unavailable_period.started_at,
                            endedAt: item.unavailable_period.ended_at
                        }
                        : null
                }))
            );
        } catch {
            setOwnerOptions([]);
        }
    }, [canEditOwner]);


    useEffect(() => {
        void fetchRequest(true);
        const intervalId = window.setInterval(() => {
            if (document.hidden || hasPendingChangesRef.current) {
                return;
            }
            void fetchRequest(false);
        }, pollIntervalMs);
        return () => window.clearInterval(intervalId);
    }, [fetchRequest]);

    useEffect(() => {
        void fetchOwners();
    }, [fetchOwners]);

    useEffect(() => {
        const ownerForPlans = (isEditMode ? ownerUserId : requestDetails?.id_user) ?? '';
        if (!ownerForPlans) {
            setPlanOptions([]);
            setPlanOptionsOwnerId(null);
            return;
        }
        if (planOptionsOwnerId === ownerForPlans) {
            return;
        }

        let isMounted = true;
        setIsPlanOptionsLoading(true);
        getPlanOptions({ ownerUserId: ownerForPlans })
            .then((items) => {
                if (!isMounted) {
                    return;
                }
                setPlanOptions(items);
                setPlanOptionsOwnerId(ownerForPlans);
            })
            .catch(() => {
                if (!isMounted) {
                    return;
                }
                setPlanOptions([]);
                setPlanOptionsOwnerId(ownerForPlans);
            })
            .finally(() => {
                if (isMounted) {
                    setIsPlanOptionsLoading(false);
                }
            });

        return () => {
            isMounted = false;
        };
    }, [isEditMode, ownerUserId, planOptionsOwnerId, requestDetails?.id_user]);

     const getSaveValidationError = (
        currentStatus: RequestStatus,
        currentDeadline: string,
        currentInitialAmount: string,
        currentFinalAmount: string
    ) => {
        const statusChanged = currentStatus !== baselineStatus;
        const ownerChanged = ownerUserId !== baselineOwnerUserId;
        const isReopen = statusChanged && baselineStatus !== 'open' && currentStatus === 'open';
        const deadlineChanged = currentDeadline !== baselineDeadline;
        const initialAmountChanged = canViewRequestAmounts && currentInitialAmount !== baselineInitialAmount;
        const finalAmountChanged = canViewRequestAmounts && currentFinalAmount !== baselineFinalAmount;
        const planChanged = planId !== baselinePlanId;
        const parsedInitialAmount = canViewRequestAmounts ? parseAmountInput(currentInitialAmount) : null;
        const parsedFinalAmount = canViewRequestAmounts ? parseAmountInput(currentFinalAmount) : null;

        const isFinalStatus = currentStatus === 'closed' || currentStatus === 'cancelled';
        if (!statusChanged && !deadlineChanged && !ownerChanged && !initialAmountChanged && !finalAmountChanged && !planChanged && !hasFileChanges) {
            return 'Нет изменений для сохранения';
        }

        if (canViewRequestAmounts) {
            if (Number.isNaN(parsedInitialAmount)) {
                return 'Укажите корректную сумму по ТЗ';
            }
            if (Number.isNaN(parsedFinalAmount)) {
                return 'Укажите корректную итоговую сумму';
            }
            if (parsedInitialAmount === null && (currentStatus === 'closed' || initialAmountChanged)) {
                return 'Укажите сумму по ТЗ';
            }
            if ((parsedInitialAmount !== null && parsedInitialAmount < 0) || (parsedFinalAmount !== null && parsedFinalAmount < 0)) {
                return 'Сумма не может быть отрицательной';
            }

            if (currentStatus === 'closed') {
                const acceptedOffer = offers.find((offer) => offer.status === 'accepted');
                if (parsedFinalAmount === null) {
                    return 'Для закрытия заявки укажите итоговую сумму';
                }
                if (!acceptedOffer) {
                    if (parsedFinalAmount !== parsedInitialAmount) {
                        return 'Для закрытия заявки без принятого КП итоговая сумма должна совпадать с суммой по ТЗ';
                    }
                } else if (acceptedOffer.offer_amount === null || acceptedOffer.offer_amount === undefined) {
                    return 'Для закрытия заявки с принятым КП у него должна быть указана сумма';
                } else if (parsedFinalAmount !== parsedInitialAmount && parsedFinalAmount !== acceptedOffer.offer_amount) {
                    return 'Итоговая сумма должна совпадать с суммой по ТЗ или с суммой принятого КП';
                }
            }
        }

        if ((deadlineChanged || isReopen) && !currentDeadline) {
            return 'При повторном открытии заявки необходимо установить дедлайн';
        }

        if (!isFinalStatus && currentDeadline && currentDeadline < todayDate) {
            return 'Дедлайн не может быть раньше текущей даты';
        }

        if (!isFinalStatus && deadlineChanged && currentStatus !== 'open' && currentStatus !== 'review') {
            return 'Для изменения дедлайна заявку необходимо повторно открыть';
        }

        if (ownerChanged && !canEditOwner) {
            return 'Изменение ответственного доступно только суперадмину и ведущему экономисту';
        }

        if (ownerChanged && ownerUserId && !ownerOptions.some((option) => option.id === ownerUserId)) {
            return 'Назначить ответственным можно только ведущего экономиста или экономиста';
        }

        const selectedOwner = ownerOptions.find((option) => option.id === ownerUserId);
        if (ownerChanged && selectedOwner?.unavailablePeriod) {
            const start = formatUnavailabilityDate(selectedOwner.unavailablePeriod.startedAt);
            const end = formatUnavailabilityDate(selectedOwner.unavailablePeriod.endedAt);
            return `Нельзя назначить ответственного: сотрудник в нерабочем статусе (${start} — ${end})`;
        }

        return null;
    };

    const effectiveDeadlineForValidation = status === 'review' ? todayDate : deadline;
    const saveValidationError = getSaveValidationError(status, effectiveDeadlineForValidation, initialAmount, finalAmount);

    const acceptedOfferId = useMemo(
        () => offers.find((offer) => offer.status === 'accepted')?.offer_id ?? null,
        [offers]
    );

    const handleSave = async () => {
        const currentRequest = requestDetails;
        if (!currentRequest || !canSaveRequestChanges) {
            return;
        }

        const statusChanged = status !== baselineStatus;
        const ownerChanged = ownerUserId !== baselineOwnerUserId;
        const planChanged = planId !== baselinePlanId;
        const parsedInitialAmount = canViewRequestAmounts ? parseAmountInput(initialAmount) : null;
        const parsedFinalAmount = canViewRequestAmounts ? parseAmountInput(finalAmount) : null;
        const parsedPlanId = planId ? Number(planId) : null;
        const initialAmountChanged = canViewRequestAmounts && initialAmount !== baselineInitialAmount;
        const finalAmountChanged = canViewRequestAmounts && finalAmount !== baselineFinalAmount;
        let effectiveDeadline = deadline;
        if (status === 'review') {
            effectiveDeadline = todayDate;
        }
        const deadlineChanged = effectiveDeadline !== baselineDeadline;

        const validationError = getSaveValidationError(status, effectiveDeadline, initialAmount, finalAmount);
        if (validationError) {
            setErrorMessage(validationError);
            setSuccessMessage(null);
            return;
        }
        setIsSaving(true);
        setErrorMessage(null);
        setSuccessMessage(null);

        try {
            await updateRequestDetails({
                requestId: currentRequest.id,
                status: statusChanged ? status : undefined,
                deadline_at: deadlineChanged ? toDeadlineIso(effectiveDeadline) : undefined,
                owner_user_id: ownerChanged ? ownerUserId : undefined,
                initial_amount: initialAmountChanged && parsedInitialAmount !== null ? parsedInitialAmount : undefined,
                final_amount: finalAmountChanged && parsedFinalAmount !== null ? parsedFinalAmount : undefined,
                id_plan: planChanged ? parsedPlanId : undefined,
            });

            await Promise.all(deletedFileIds.map((fileId) => deleteRequestFile(currentRequest.id, fileId)));
            if (newFile) {
                await uploadRequestFile(currentRequest.id, newFile);
            }

            const refreshed = await getRequestDetails(currentRequest.id);
            syncRequestState(refreshed, true);
            setIsEditMode(false);
            setDeletedFileIds([]);
            setNewFile(null);
            setSuccessMessage('Изменения сохранены');
        } catch (error) {
            setErrorMessage(error instanceof Error ? error.message : 'Не удалось сохранить изменения');
        } finally {
            setIsSaving(false);
        }
    };

    const handleOfferStatusChange = async (offerId: number, value: OfferDecisionStatus) => {
        const targetOffer = offers.find((offer) => offer.offer_id === offerId);
        if (!targetOffer || (!targetOffer.actions.accept && !targetOffer.actions.reject)) {
            return;
        }
        
        const previousStatus = offersStatusMap[offerId] ?? '';

        setOffersStatusMap((prev) => ({
            ...prev,
            [offerId]: value
        }));

        if (!value) {
            return;
        }
        if (value === 'accepted' && acceptedOfferId && acceptedOfferId !== offerId) {
            setOffersStatusMap((prev) => ({
                ...prev,
                [offerId]: previousStatus
            }));
            setOffersError('Нельзя одобрить более одного КП в рамках одной заявки');
            return;
        }

        const confirmMessage =
            value === 'accepted'
                ? 'Если принять это КП, остальные КП по заявке автоматически получат статус «Отказано». Продолжить?'
                : 'Вы уверены, что хотите изменить статус КП на «Отказано»?';

        const isConfirmed = window.confirm(confirmMessage);

        if (!isConfirmed) {
            setOffersStatusMap((prev) => ({
                ...prev,
                [offerId]: previousStatus
            }));
            return;
        }

        try {
            const response = await updateOfferStatus({
                offer_id: offerId,
                status: value
            });
            setOffers((prev) =>
                prev.map((offer) =>
                    offer.offer_id === offerId
                        ? { ...offer, status: response.offer.status }
                        : offer
                )
            );
            setOffersStatusMap((prev) => ({
                ...prev,
                [offerId]: normalizeOfferStatus(response.offer.status)
            }));
        } catch (error) {
            setOffersStatusMap((prev) => ({
                ...prev,
                [offerId]: previousStatus
            }));
            setOffersError(error instanceof Error ? error.message : 'Не удалось обновить статус КП');
        }
    };


    const handleDeletedAlertViewed = async () => {
        if (!hasDeletedAlert || !requestDetails) {
            return;
        }

        setIsClearingDeletedAlert(true);
        setErrorMessage(null);
        try {
            const response = await markDeletedAlertViewed({
                request_id: requestDetails.id
            });
            setRequestDetails((prev) => {
                if (!prev) {
                    return prev;
                }
                return {
                    ...prev,
                    count_deleted_alert: response.request_offer_stats.count_deleted_alert,
                    updated_at: response.request_offer_stats.updated_at ?? prev.updated_at
                };
            });
        } catch (error) {
            setErrorMessage(error instanceof Error ? error.message : 'Не удалось отметить уведомление');
        } finally {
            setIsClearingDeletedAlert(false);
        }
    };

    const handleDownload = async (downloadUrl: string, fileName: string) => {
        try {
            await downloadFile(downloadUrl, fileName);
        } catch (error) {
            setErrorMessage(error instanceof Error ? error.message : 'Не удалось скачать файл');
        }
    };

    const handleRemoveExistingFile = (fileId: number) => {
        setExistingFiles((prev) => prev.filter((file) => file.id !== fileId));
        setDeletedFileIds((prev) => (prev.includes(fileId) ? prev : [...prev, fileId]));
    };

    const handleSendAdditionalEmails = async () => {
        if (!requestDetails || !canSendAdditionalEmails) {
            return;
        }

        const nextAdditionalEmails = additionalEmailsFieldRef.current?.commitPendingInput();
        if (nextAdditionalEmails === null) {
            return;
        }

        if (!nextAdditionalEmails || nextAdditionalEmails.length === 0) {
            setErrorMessage('Добавьте хотя бы один e-mail для отправки');
            setSuccessMessage(null);
            return;
        }

        setIsSendingEmails(true);
        setErrorMessage(null);
        setSuccessMessage(null);

        try {
            const response = await sendRequestEmailNotifications({
                requestId: requestDetails.id,
                additional_emails: nextAdditionalEmails
            });
            setAdditionalEmails(response.data.sent_to);
            setSuccessMessage(
                response.data.sent_to.length === 1
                    ? `Письмо отправлено: ${response.data.sent_to[0]}`
                    : `Писем отправлено: ${response.data.sent_to.length}`
            );
        } catch (error) {
            setErrorMessage(error instanceof Error ? error.message : 'Не удалось отправить письма');
            setSuccessMessage(null);
        } finally {
            setIsSendingEmails(false);
        }
    };

    const handleCancelEditing = () => {
        setStatus(baselineStatus);
        setDeadline(baselineDeadline);
        setOwnerUserId(baselineOwnerUserId);
        setInitialAmount(baselineInitialAmount);
        setFinalAmount(baselineFinalAmount);
        setPlanId(baselinePlanId);
        setDeletedFileIds([]);
        setNewFile(null);
        setIsEditMode(false);
        setErrorMessage(null);
        setSuccessMessage(null);
    };

    const ownerField = canEditOwner && isEditMode ? (
        <Select
            size="small"
            value={ownerUserId}
            fullWidth
            renderValue={(selected) =>
                ownerOptions.find((option) => option.id === selected)?.label
                ?? requestDetails?.owner_full_name
                ?? String(selected ?? '')
            }
            onChange={(event) => setOwnerUserId(event.target.value)}
        >
            {ownerOptions.map((option) => (
                <UnavailableAwareMenuItem
                    key={option.id}
                    value={option.id}
                    label={option.label}
                    unavailablePeriod={option.unavailablePeriod}
                />
            ))}
        </Select>
    ) : (
        <TextField
            size="small"
            value={requestDetails?.owner_full_name ?? requestDetails?.id_user ?? '-'}
            fullWidth
            InputProps={{ readOnly: true }}
        />
    );
    const selectedPlanOption = planOptions.find((option) => String(option.plan_id) === planId);
    const planDisplayLabel = selectedPlanOption
        ? `${selectedPlanOption.plan_name} (${selectedPlanOption.user_name})`
        : planId
            ? `План #${planId}`
            : 'Без плана';
    const descriptionText = requestDetails?.description?.trim() ?? '';
    const canExpandDescription = isDescriptionOverflowing;
    const handleStatusSelection = (nextStatus: RequestStatus) => {
        if (nextStatus !== status) {
            const isConfirmed = window.confirm(
                `Вы уверены, что хотите изменить статус заявки на «${statusOptions.find((option) => option.value === nextStatus)?.label ?? nextStatus}»?`
            );
            if (!isConfirmed) {
                return;
            }
        }
        setStatus(nextStatus);
        if (nextStatus === 'review') {
            setDeadline(todayDate);
        }
    };

    useEffect(() => {
        const element = descriptionTextRef.current;
        if (!element) {
            setIsDescriptionOverflowing(false);
            return;
        }
        if (isDescriptionExpanded) {
            return;
        }

        const checkOverflow = () => {
            setIsDescriptionOverflowing(element.scrollHeight - element.clientHeight > 1);
        };

        checkOverflow();
        window.addEventListener('resize', checkOverflow);
        return () => window.removeEventListener('resize', checkOverflow);
    }, [descriptionText, isDescriptionExpanded]);

    useEffect(() => {
        if (!hasPendingChanges) {
            return;
        }

        const handleBeforeUnload = (event: BeforeUnloadEvent) => {
            event.preventDefault();
            event.returnValue = '';
        };

        window.addEventListener('beforeunload', handleBeforeUnload);
        return () => window.removeEventListener('beforeunload', handleBeforeUnload);
    }, [hasPendingChanges]);

    if (!requestDetails) {
        return (
            <Box>
                <Typography variant="h6" mb={2}>
                    Нет данных для отображения заявки.
                </Typography>
                <Button variant="outlined" onClick={() => navigate('/requests')}>
                    Вернуться к заявкам
                </Button>
            </Box>
        );
    }

    return (
        <Box>
            {hasPendingChanges && (
                <Typography role="status" color="warning.main" sx={{ mb: 2 }}>
                    Есть несохраненные изменения. При уходе со страницы они будут потеряны.
                </Typography>
            )}
            {hasPendingChanges && saveValidationError && (
                <Alert severity="warning" sx={{ mb: 2 }}>
                    {saveValidationError}
                </Alert>
            )}
            {errorMessage && (
                <Alert severity="error" onClose={() => setErrorMessage(null)} sx={{ mb: 2 }}>
                    {errorMessage}
                </Alert>
            )}
            {successMessage && (
                <Alert severity="success" onClose={() => setSuccessMessage(null)} sx={{ mb: 2 }}>
                    {successMessage}
                </Alert>
            )}

            <RequestDetailsMainCard
                requestId={requestDetails.id}
                status={status}
                statusOptions={statusOptions}
                statusColor={statusColor}
                canEditRequest={canEditRequest}
                isEditMode={isEditMode}
                onStatusChange={handleStatusSelection}
                descriptionText={descriptionText}
                descriptionTextRef={descriptionTextRef}
                canExpandDescription={canExpandDescription}
                isDescriptionExpanded={isDescriptionExpanded}
                onToggleDescription={() => setIsDescriptionExpanded((prev) => !prev)}
                ownerField={ownerField}
                existingFiles={existingFiles}
                canDeleteRequestFiles={canDeleteRequestFiles}
                onDownloadFile={(downloadUrl, fileName) => void handleDownload(downloadUrl, fileName)}
                onRemoveExistingFile={handleRemoveExistingFile}
                newFile={newFile}
                onClearNewFile={() => setNewFile(null)}
                canUploadRequestFiles={canUploadRequestFiles}
                onNewFileSelected={setNewFile}
                canViewRequestAmounts={canViewRequestAmounts}
                deadline={deadline}
                initialAmount={initialAmount}
                finalAmount={finalAmount}
                onDeadlineChange={setDeadline}
                onInitialAmountChange={setInitialAmount}
                onFinalAmountChange={setFinalAmount}
                requestCreatedAt={requestDetails.created_at ?? null}
                requestClosedAt={requestDetails.closed_at ?? null}
                requestDeadlineAt={requestDetails.deadline_at ?? null}
                requestOfferId={requestDetails.id_offer ?? '-'}
                requestUpdatedAt={requestDetails.updated_at ?? null}
                isSaving={isSaving}
                canSaveRequestChanges={canSaveRequestChanges}
                hasPendingChanges={hasPendingChanges}
                hasValidationError={Boolean(saveValidationError)}
                canEnterEditMode={canEnterEditMode}
                onCancelEditing={handleCancelEditing}
                onSave={() => void handleSave()}
                onStartEdit={() => setIsEditMode(true)}
            />

            <Box
                sx={(themeValue) => ({
                    mt: 2,
                    borderRadius: `${themeValue.acomShape.panelRadius}px`,
                    border: `1px solid ${themeValue.palette.divider}`,
                    backgroundColor: themeValue.palette.background.paper,
                    px: { xs: 2, md: 3 },
                    py: { xs: 1.5, md: 2 },
                })}
            >
                <Stack spacing={0.75}>
                    <Typography variant="body2" color="text.secondary">
                        План заявки
                    </Typography>
                    {canEditRequest && isEditMode ? (
                        <Select
                            size="small"
                            value={planId}
                            displayEmpty
                            onChange={(event) => setPlanId(String(event.target.value))}
                            disabled={isPlanOptionsLoading}
                        >
                            <MenuItem value="">Без плана</MenuItem>
                            {planId && !planOptions.some((option) => String(option.plan_id) === planId) ? (
                                <MenuItem value={planId}>{planDisplayLabel}</MenuItem>
                            ) : null}
                            {planOptions.map((option) => (
                                <MenuItem
                                    key={option.plan_id}
                                    value={String(option.plan_id)}
                                    disabled={option.is_closed}
                                >
                                    {option.plan_name} ({option.user_name})
                                </MenuItem>
                            ))}
                        </Select>
                    ) : (
                        <TextField
                            size="small"
                            value={planDisplayLabel}
                            fullWidth
                            InputProps={{ readOnly: true }}
                        />
                    )}
                </Stack>
            </Box>

            {status === 'open' && (
                <Box sx={{ mt: 2.5 }}>
                    <ToggleSection
                        title="Дополнительная рассылка на электронную почту"
                        checked={additionalEmailsEnabled}
                        disabled={isAdditionalEmailsFieldUnavailable}
                        onChange={(_event, checked) => {
                            setAdditionalEmailsEnabled(checked);
                            if (!checked) {
                                setAdditionalEmails([]);
                            }
                        }}
                        description="Для уже созданной открытой заявки письма будут отправлены только на адреса, которые вы добавите вручную."
                    >
                        <Stack spacing={1.5}>
                            <AdditionalEmailsField
                                ref={additionalEmailsFieldRef}
                                emails={additionalEmails}
                                onChange={setAdditionalEmails}
                                hideHeader
                                addButtonVariant="icon"
                                disabled={isAdditionalEmailsFieldUnavailable}
                                helperText="Можно добавить несколько адресов через запятую."
                                containerSx={{
                                    mt: 0,
                                    opacity: isAdditionalEmailsFieldUnavailable ? 0.5 : 1,
                                    transition: 'opacity 0.2s ease'
                                }}
                            />
                            <Button
                                variant="outlined"
                                sx={{ width: 'fit-content' }}
                                onClick={() => void handleSendAdditionalEmails()}
                                disabled={isAdditionalEmailsFieldUnavailable}
                            >
                                {isSendingEmails ? 'Отправка...' : 'Отправить'}
                            </Button>
                        </Stack>
                    </ToggleSection>
                </Box>
            )}

            {hasDeletedAlert && canMarkDeletedAlertViewed && (
                <Button
                    variant="contained"
                    sx={(theme) => ({
                        mt: 2,
                        paddingX: 3,
                        width: 'fit-content',
                        backgroundColor: theme.palette.error.main,
                        color: theme.palette.error.contrastText,
                        boxShadow: 'none',
                        '&:hover': { backgroundColor: theme.palette.error.dark, boxShadow: 'none' },
                        '&:disabled': {
                            backgroundColor: theme.palette.error.light,
                            color: theme.palette.error.contrastText
                        }
                    })}
                    onClick={() => void handleDeletedAlertViewed()}
                    disabled={isClearingDeletedAlert}
                >
                    {isClearingDeletedAlert ? 'Отмечаем...' : 'Уведомлен об отмене сделки'}
                </Button>
            )}

            <Box sx={{ marginTop: 4 }}>
                <OffersTable
                    offers={offers}
                    statusMap={offersStatusMap}
                    acceptedOfferId={acceptedOfferId}
                    isLoading={offersLoading}
                    errorMessage={offersError}
                    statusOptions={offerStatusOptions}
                    onStatusChange={(offerId, value) => void handleOfferStatusChange(offerId, value)}
                    onOpenWorkspace={(offerId) => navigate(`/offers/${offerId}/workspace?requestId=${requestDetails.id}`)}
                    onDownloadFile={(downloadUrl, fileName) => void handleDownload(downloadUrl, fileName)}
                    canChangeStatus={canChangeOfferStatus}
                    onAddClick={canCreateManualOffer ? () => setIsManualOfferDialogOpen(true) : undefined}
                />
            </Box>
            <CreateManualOfferDialog
                open={isManualOfferDialogOpen}
                requestId={requestDetails.id}
                onClose={() => setIsManualOfferDialogOpen(false)}
                onCreated={(workspacePath) => {
                    setIsManualOfferDialogOpen(false);
                    const separator = workspacePath.includes('?') ? '&' : '?';
                    navigate(`${workspacePath}${separator}requestId=${requestDetails.id}`);
                }}
            />
        </Box>
    );
};
