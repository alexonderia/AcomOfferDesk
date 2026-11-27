import { zodResolver } from '@hookform/resolvers/zod';
import CloudUploadOutlinedIcon from '@mui/icons-material/CloudUploadOutlined';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import {
  Autocomplete,
  Box,
  Button,
  Chip,
  Dialog,
  DialogContent,
  FormControl,
  FormHelperText,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { alpha, type Theme } from '@mui/material/styles';
import { useEffect, useMemo, useRef, useState, type DragEvent } from 'react';
import { Controller } from 'react-hook-form';
import { textFieldAutocompleteProps, useLiveValidatedForm } from '@shared/lib/forms';
import { Navigate, useNavigate } from 'react-router-dom';
import { z } from 'zod';
import { useAuth } from '@app/providers/AuthProvider';
import { checkRequestIdAvailability } from '@shared/api/requests/checkRequestIdAvailability';
import { createRequest } from '@shared/api/requests/createRequest';
import { previewRequestEmails } from '@shared/api/requests/previewRequestEmails';
import { prepareRequestSpecification, type PreparedRequestSpecification } from '@shared/api/requests/prepareRequestSpecification';
import { useRequestEmailReview } from '@features/request-email/model/useRequestEmailReview';
import { RequestEmailReviewDialog } from '@features/request-email/ui/RequestEmailReviewDialog';
import { RequestUploadList } from '@features/request-details/ui/RequestUploadList';
import { getNormativeFiles } from '@shared/api/normative/getNormativeFiles';
import type { NormativeFileItem } from '@shared/api/normative/types';
import { getRequestContractors, type RequestContractorItem } from '@shared/api/users/getRequestContractors';
import { hasPermission } from '@shared/auth/permissions';
import { AdditionalEmailsField, type AdditionalEmailsFieldHandle } from '@shared/components/AdditionalEmailsField';
import { DatePickerField } from '@shared/components/DatePickerField';
import { FilePreviewTrigger } from '@shared/components/file-preview/FilePreviewTrigger';
import { RequiredFieldLabel } from '@shared/components/forms/RequiredFieldLabel';
import { ToggleSection } from '@shared/components/ToggleSection';
import {
  ALLOWED_UPLOAD_FILE_INPUT_ACCEPT,
  ALLOWED_UPLOAD_FILE_TYPES_LABEL,
  MAX_UPLOAD_FILE_SIZE_MB,
  getFileKey,
  mergeUniqueFiles,
} from '@shared/lib/files';
import { useSystemToasts } from '@shared/ui/toasts';
import { dialogContentSx, dialogPaperSx } from '@shared/ui/dialogSurface';

const normalizeAmountValue = (value: string) => value.trim().replace(',', '.');
const isValidAmountValue = (value: string) => {
  const normalized = normalizeAmountValue(value);
  if (!normalized) {
    return false;
  }

  const parsed = Number(normalized);
  return Number.isFinite(parsed) && parsed >= 0;
};

const schema = z.object({
  requestNumber: z
    .string()
    .trim()
    .min(1, 'Укажите номер заявки')
    .refine((value) => value.trim().length > 0, 'Укажите номер заявки'),
  initialAmount: z.string().trim().min(1, 'Укажите сумму по ТЗ').refine(isValidAmountValue, 'Укажите корректную сумму'),
  description: z.string().max(3000, 'Максимум 3000 символов').optional(),
  deadlineAt: z.string().min(1, 'Укажите дату завершения сбора откликов'),
  normativeFileId: z.number({ error: 'Выберите нормативный документ' }).int().positive('Выберите нормативный документ'),
  files: z.array(z.instanceof(File)).min(1, 'Прикрепите исходный договор').max(5, 'Можно прикрепить до 5 исходных файлов')
    .refine((files) => files.reduce((size, file) => size + file.size, 0) <= 15 * 1024 * 1024, 'Общий размер исходников — до 15 МБ'),
  extractionKeys: z.array(z.string()).min(1, 'Выберите хотя бы один файл для формирования заявки'),
  hiddenFileKeys: z.array(z.string()),
  additionalEmails: z.array(z.string().email('Введите корректный email')),
  hiddenContractorIds: z.array(z.string().min(1)),
});

type FormValues = z.infer<typeof schema>;
type ReviewSnapshot = FormValues & { specification?: PreparedRequestSpecification };
const getPublicSourceFiles = (values: FormValues) => values.files.filter((file) => !values.hiddenFileKeys.includes(getFileKey(file)));

const getContractorOptionLabel = (contractor: RequestContractorItem) => {
  const primaryLabel = contractor.company_name?.trim() || contractor.full_name?.trim() || contractor.user_id;
  const secondaryLabel = contractor.company_mail?.trim() || contractor.mail?.trim() || contractor.user_id;
  return `${primaryLabel} (${secondaryLabel})`;
};

export const CreateRequestPage = () => {
  const { session } = useAuth();
  const navigate = useNavigate();
  const canCreateRequest = hasPermission(session, 'requests.create');
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const additionalEmailsFieldRef = useRef<AdditionalEmailsFieldHandle | null>(null);
  const todayDate = useMemo(() => {
    const now = new Date();
    const offsetMs = now.getTimezoneOffset() * 60000;
    return new Date(now.getTime() - offsetMs).toISOString().split('T')[0];
  }, []);

  const [isLoadingNormativeFiles, setIsLoadingNormativeFiles] = useState(true);
  const [actualNormativeFiles, setActualNormativeFiles] = useState<NormativeFileItem[]>([]);
  const [isSubmittingRequest, setIsSubmittingRequest] = useState(false);
  const [showSlowFileCheckHint, setShowSlowFileCheckHint] = useState(false);
  const [requestIdStatus, setRequestIdStatus] = useState<{ available: boolean; detail: string } | null>(null);
  const [isCheckingRequestId, setIsCheckingRequestId] = useState(false);
  const [contractorOptions, setContractorOptions] = useState<RequestContractorItem[]>([]);
  const [isLoadingContractors, setIsLoadingContractors] = useState(false);
  const [isDraggingFiles, setIsDraggingFiles] = useState(false);
  const [hideFromContractorsEnabled, setHideFromContractorsEnabled] = useState(false);
  const [additionalEmailsEnabled, setAdditionalEmailsEnabled] = useState(false);
  const { review, isLoadingReview, prepareReview, closeReview } = useRequestEmailReview<ReviewSnapshot>();
  const { showErrorToast, showSuccessToast, showSystemToast } = useSystemToasts();

  const {
    control,
    register,
    handleSubmit,
    watch,
    setValue,
    setError,
    clearErrors,
    formState: { errors },
  } = useLiveValidatedForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      requestNumber: '',
      initialAmount: '',
      description: '',
      deadlineAt: todayDate,
      normativeFileId: undefined,
      files: [],
      extractionKeys: [],
      hiddenFileKeys: [],
      additionalEmails: [],
      hiddenContractorIds: [],
    },
  });

  const requestNumberValue = watch('requestNumber');
  const normativeFileId = watch('normativeFileId');
  const selectedNormativeFile = actualNormativeFiles.find((item) => item.id === normativeFileId);
  const files = watch('files');
  const extractionKeys = watch('extractionKeys');
  const hiddenFileKeys = watch('hiddenFileKeys');
  const additionalEmails = watch('additionalEmails');
  const hiddenContractorIds = watch('hiddenContractorIds');
  const hiddenContractors = useMemo(
    () => contractorOptions.filter((contractor) => hiddenContractorIds.includes(contractor.user_id)),
    [contractorOptions, hiddenContractorIds]
  );

  const requestNumberRef = useRef(requestNumberValue);
  requestNumberRef.current = requestNumberValue;

  useEffect(() => {
    let isMounted = true;

    const loadNormativeFiles = async () => {
      setIsLoadingNormativeFiles(true);
      try {
        const items = await getNormativeFiles('actual');
        if (!isMounted) {
          return;
        }
        setActualNormativeFiles(items);
        if (items.length === 1) {
          setValue('normativeFileId', items[0].id, { shouldValidate: true });
        }
      } catch (error) {
        if (isMounted) {
          showErrorToast(error instanceof Error ? error.message : 'Не удалось загрузить нормативные документы');
        }
      } finally {
        if (isMounted) {
          setIsLoadingNormativeFiles(false);
        }
      }
    };

    void loadNormativeFiles();

    return () => {
      isMounted = false;
    };
  }, [setValue, showErrorToast]);

  useEffect(() => {
    const normalizedRequestNumber = requestNumberValue.trim();
    if (!normalizedRequestNumber) {
      setRequestIdStatus(null);
      setIsCheckingRequestId(false);
      return;
    }

    setIsCheckingRequestId(true);
    setRequestIdStatus(null);

    const timer = setTimeout(async () => {
      const checkedValue = normalizedRequestNumber;
      try {
        const result = await checkRequestIdAvailability(checkedValue);
        if (requestNumberRef.current.trim() !== checkedValue) {
          return;
        }
        setRequestIdStatus({
          available: result.available,
          detail: result.detail ?? (result.available ? 'Номер заявки свободен' : 'Заявка с таким номером уже существует'),
        });
      } catch {
        if (requestNumberRef.current.trim() !== checkedValue) {
          return;
        }
        setRequestIdStatus({
          available: false,
          detail: 'Не удалось проверить номер заявки. Повторите позже.',
        });
      } finally {
        if (requestNumberRef.current.trim() === checkedValue) {
          setIsCheckingRequestId(false);
        }
      }
    }, 400);

    return () => clearTimeout(timer);
  }, [requestNumberValue]);

  useEffect(() => {
    if (!requestIdStatus) {
      return;
    }

    if (requestIdStatus.available) {
      clearErrors('requestNumber');
      return;
    }

    if (requestNumberValue.trim().length > 0) {
      setError('requestNumber', { type: 'manual', message: requestIdStatus.detail });
    }
  }, [requestIdStatus, requestNumberValue, clearErrors, setError]);

  const isRequestNumberBlocked =
    !requestNumberValue.trim()
    || isCheckingRequestId
    || !requestIdStatus
    || !requestIdStatus.available;

  const isRequestNumberAvailable =
    Boolean(requestNumberValue.trim()) && Boolean(requestIdStatus?.available) && !isCheckingRequestId;

  useEffect(() => {
    let isMounted = true;

    const loadContractors = async () => {
      setIsLoadingContractors(true);
      try {
        const response = await getRequestContractors();
        if (isMounted) {
          setContractorOptions(response.items);
        }
      } catch (error) {
        if (isMounted) {
          showErrorToast(error instanceof Error ? error.message : 'Ошибка загрузки контрагентов');
        }
      } finally {
        if (isMounted) {
          setIsLoadingContractors(false);
        }
      }
    };

    void loadContractors();

    return () => {
      isMounted = false;
    };
  }, [showErrorToast]);

  const updateFiles = (nextFiles: File[]) => {
    setValue('hiddenFileKeys', hiddenFileKeys.filter((key) => nextFiles.some((file) => getFileKey(file) === key)), {
      shouldDirty: true, shouldValidate: true,
    });
    setValue('extractionKeys', extractionKeys.filter((key) => nextFiles.some((file) => getFileKey(file) === key)), {
      shouldDirty: true, shouldValidate: true,
    });
    setValue('files', nextFiles, {
      shouldDirty: true,
      shouldTouch: true,
      shouldValidate: true,
    });
  };

  const handleFilesAdded = (addedFiles: File[]) => {
    const merged = mergeUniqueFiles(files, addedFiles);
    updateFiles(merged);
    setValue('hiddenFileKeys', [
      ...hiddenFileKeys,
      ...merged.filter((file) => !files.some((existing) => getFileKey(existing) === getFileKey(file))).map(getFileKey),
    ], { shouldDirty: true, shouldValidate: true });
    if (!files.length && merged.length) {
      setValue('extractionKeys', [getFileKey(merged[0])], { shouldDirty: true, shouldValidate: true });
    }
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDraggingFiles(false);
    handleFilesAdded(Array.from(event.dataTransfer.files ?? []));
  };

  const hasActualNormativeFiles = actualNormativeFiles.length > 0;
  const isSubmitBlocked =
    isRequestNumberBlocked
    || !hasActualNormativeFiles
    || isLoadingNormativeFiles
    || !normativeFileId;

  useEffect(() => {
    if (isLoadingNormativeFiles || hasActualNormativeFiles) {
      return;
    }

    showSystemToast({
      severity: 'warning',
      message: 'Нет актуальных нормативных документов. Обратитесь к ведущему экономисту.',
    });
  }, [hasActualNormativeFiles, isLoadingNormativeFiles, showSystemToast]);

  useEffect(() => {
    if (!isSubmittingRequest) {
      setShowSlowFileCheckHint(false);
      return;
    }

    const timer = window.setTimeout(() => {
      setShowSlowFileCheckHint(true);
    }, 2000);

    return () => {
      window.clearTimeout(timer);
    };
  }, [isSubmittingRequest]);

  const handleSubmitForm = async (values: FormValues) => {
    if (isLoadingReview || isSubmittingRequest || isSubmitBlocked) return;
    if (!values.normativeFileId) {
      setError('normativeFileId', { type: 'manual', message: 'Выберите нормативный документ' });
      return;
    }

    if (!values.files.length) {
      setError('files', { type: 'manual', message: 'Прикрепите файл заявки' });
      return;
    }

    const normalizedRequestNumber = values.requestNumber.trim();
    if (!normalizedRequestNumber) {
      setError('requestNumber', { type: 'manual', message: 'Укажите номер заявки' });
      return;
    }

    if (requestIdStatus && !requestIdStatus.available) {
      setError('requestNumber', { type: 'manual', message: requestIdStatus.detail });
      return;
    }

    const nextAdditionalEmails = additionalEmailsEnabled
      ? additionalEmailsFieldRef.current?.commitPendingInput()
      : [];

    if (nextAdditionalEmails === null) {
      return;
    }

    const snapshot: FormValues = {
      ...values,
      files: [...values.files],
      extractionKeys: [...values.extractionKeys],
      hiddenFileKeys: [...values.hiddenFileKeys],
      additionalEmails: [...(nextAdditionalEmails ?? values.additionalEmails)],
      hiddenContractorIds: hideFromContractorsEnabled ? [...values.hiddenContractorIds] : [],
    };
    try {
      await prepareReview(snapshot, async (signal) => {
        const extractionIndices = snapshot.files.flatMap((file, index) => snapshot.extractionKeys.includes(getFileKey(file)) ? [index] : []);
        const publicSourceIndices = snapshot.files.flatMap((file, index) => snapshot.hiddenFileKeys.includes(getFileKey(file)) ? [] : [index]);
        const specification = await prepareRequestSpecification(normalizedRequestNumber, snapshot.files, extractionIndices, publicSourceIndices, signal);
        const preview = session?.emailEnabled === false ? { messages: [], warnings: ['Почтовый сервис отключён. Письма не будут отправлены.'] } : await previewRequestEmails({
        request_id: normalizedRequestNumber,
        description: snapshot.description?.trim() || null,
        deadline_at: `${snapshot.deadlineAt}T23:59:59`,
        normative_file_id: snapshot.normativeFileId,
        files: [...getPublicSourceFiles(snapshot), specification.file].map((file) => ({ name: file.name, size_bytes: file.size })),
        additional_emails: snapshot.additionalEmails,
        hidden_contractor_ids: snapshot.hiddenContractorIds,
        }, signal);
        return { preview, snapshot: { ...snapshot, specification } };
      });
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') return;
      showErrorToast(error instanceof Error ? error.message : 'Не удалось подготовить проверку писем');
    }
  };

  const handleConfirmCreation = async () => {
    if (!review?.snapshot.specification || isSubmittingRequest) return;
    const values = review.snapshot;
    setIsSubmittingRequest(true);

    try {
      await createRequest({
        id: values.requestNumber.trim(),
        normative_file_id: values.normativeFileId,
        description: values.description?.trim() || null,
        deadline_at: `${values.deadlineAt}T23:59:59`,
        initial_amount: normalizeAmountValue(values.initialAmount),
        files: [review.snapshot.specification.file],
        source_files: values.files,
        specification_confirmation: review.snapshot.specification.confirmation,
        additional_emails: values.additionalEmails,
        hidden_contractor_ids: values.hiddenContractorIds,
      });
      showSuccessToast('Заявка создана');
      navigate('/requests');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Не удалось создать заявку';
      if (message.includes('Заявка с таким номером уже существует') || message.toLowerCase().includes('already exists')) {
        setError('requestNumber', { type: 'manual', message: 'Заявка с таким номером уже существует' });
        setRequestIdStatus({ available: false, detail: 'Заявка с таким номером уже существует' });
      }
      showErrorToast(message);
    } finally {
      setIsSubmittingRequest(false);
    }
  };

  if (!canCreateRequest) {
    return <Navigate to="/requests" replace />;
  }

  return (
    <>
    <Dialog
      open
      onClose={() => { if (!isSubmittingRequest && !isLoadingReview) navigate('/requests'); }}
      fullWidth
      maxWidth="sm"
      PaperProps={{
        sx: dialogPaperSx,
      }}
    >
      <DialogContent sx={dialogContentSx}>
        <Box component="form" onSubmit={handleSubmit(handleSubmitForm)}>
          <Stack spacing={2}>
            <Typography variant="h5" fontWeight={600} lineHeight={1}>
              Новая заявка
            </Typography>

            <Stack spacing={1}>
              <Typography variant="subtitle1" fontWeight={600}>
                <RequiredFieldLabel label="Номер заявки" isValid={isRequestNumberAvailable && !errors.requestNumber} />
              </Typography>
              <TextField
                placeholder="Например: 2026-001"
                fullWidth
                error={Boolean(errors.requestNumber)}
                helperText={
                  errors.requestNumber?.message
                  ?? (isCheckingRequestId ? 'Проверяем номер заявки...' : undefined)
                }
                {...textFieldAutocompleteProps('requestNumber')}
                inputProps={{ ...textFieldAutocompleteProps('requestNumber').inputProps, 'aria-label': 'Номер заявки', 'aria-required': true }}
                {...register('requestNumber', {
                  onChange: () => {
                    clearErrors('requestNumber');
                    setRequestIdStatus(null);
                  },
                })}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 1,
                    backgroundColor: 'background.paper',
                  },
                }}
              />
            </Stack>

            <Stack spacing={1}>
              <Typography variant="subtitle1" fontWeight={600}>
                Описание
              </Typography>
              <TextField
                placeholder="Кратко опишите содержание заявки"
                multiline
                minRows={3}
                fullWidth
                error={Boolean(errors.description)}
                helperText={errors.description?.message}
                {...textFieldAutocompleteProps('description')}
                {...register('description')}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 1,
                    backgroundColor: 'background.paper',
                    alignItems: 'flex-start',
                  },
                  '& .MuiOutlinedInput-input::placeholder': {
                    opacity: 1,
                  },
                }}
              />
            </Stack>

            <Stack
              direction={{ xs: 'column', sm: 'row' }}
              spacing={{ xs: 1, sm: 1 }}
              justifyContent="space-between"
              alignItems={{ xs: 'stretch', sm: 'center' }}
            >
              <Box>
                <Typography variant="subtitle1" fontWeight={600}>
                  <RequiredFieldLabel label="Дата завершения сбора откликов" isValid={Boolean(watch('deadlineAt')) && !errors.deadlineAt} />
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  (до 23:59)
                </Typography>
              </Box>
              <DatePickerField
                inputProps={{ 'aria-label': 'Дата завершения сбора откликов', 'aria-required': true }}
                value={watch('deadlineAt')}
                onChange={(value) => {
                  setValue('deadlineAt', value, {
                    shouldDirty: true,
                    shouldTouch: true,
                    shouldValidate: true,
                  });
                }}
                error={Boolean(errors.deadlineAt)}
                helperText={errors.deadlineAt?.message}
                showDropdownIcon={false}
                allowClear={false}
                minWidth={{ xs: '100%', sm: 206 }}
                sx={{
                  '& .MuiOutlinedInput-root': { borderRadius: 1 },
                  '& .MuiFormHelperText-root': { maxWidth: 206 },
                }}
              />
            </Stack>

            <Stack spacing={1}>
              <Typography variant="subtitle1" fontWeight={600}>
                <RequiredFieldLabel label="Сумма по ТЗ" isValid={schema.shape.initialAmount.safeParse(watch('initialAmount')).success} />
              </Typography>
              <TextField
                placeholder="Укажите сумму в рублях"
                fullWidth
                error={Boolean(errors.initialAmount)}
                helperText={errors.initialAmount?.message ?? 'Значение «Сумма по ТЗ» используется для расчета экономии по заявке.'}
                {...textFieldAutocompleteProps('initialAmount')}
                {...register('initialAmount')}
                inputProps={{ min: 0, step: '0.01', inputMode: 'decimal', autoComplete: 'off', 'aria-label': 'Сумма по ТЗ', 'aria-required': true }}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 1,
                    backgroundColor: 'background.paper',
                  },
                }}
              />
            </Stack>

            <Stack spacing={1}>
              <Typography variant="subtitle1" fontWeight={600}>
                Нормативный документ
              </Typography>
              <FormControl fullWidth error={Boolean(errors.normativeFileId)}>
                <InputLabel id="normative-file-label"><RequiredFieldLabel label="Нормативный документ" isValid={Boolean(selectedNormativeFile)} /></InputLabel>
                <Controller
                  control={control}
                  name="normativeFileId"
                  render={({ field }) => (
                    <Select
                      labelId="normative-file-label"
                      label={<RequiredFieldLabel label="Нормативный документ" isValid={Boolean(selectedNormativeFile)} />}
                      inputProps={{ 'aria-required': true }}
                      value={field.value ?? ''}
                      disabled={isLoadingNormativeFiles || !hasActualNormativeFiles}
                      onChange={(event) => {
                        const value = Number(event.target.value);
                        field.onChange(Number.isFinite(value) ? value : undefined);
                      }}
                      sx={{
                        borderRadius: 1,
                        backgroundColor: 'background.paper',
                      }}
                    >
                      {actualNormativeFiles.map((item) => (
                        <MenuItem key={item.id} value={item.id}>
                          {item.original_name}
                        </MenuItem>
                      ))}
                    </Select>
                  )}
                />
                <FormHelperText>
                  {errors.normativeFileId?.message
                    ?? (isLoadingNormativeFiles
                      ? 'Загружаем список нормативных документов...'
                      : !hasActualNormativeFiles
                        ? 'Нет актуальных нормативных документов. Создание заявки недоступно.'
                        : 'Выберите актуальный нормативный документ')}
                </FormHelperText>
              </FormControl>
              {selectedNormativeFile ? <FilePreviewTrigger source={{ name: selectedNormativeFile.original_name, downloadUrl: selectedNormativeFile.download_url }}>
                  {(openPreview) => <Button variant="outlined" size="small" onClick={openPreview} sx={{ alignSelf: 'flex-start' }}>Предпросмотр нормативного документа</Button>}
                </FilePreviewTrigger> : null}
            </Stack>

            <Stack spacing={1}>
              <Typography variant="subtitle1" fontWeight={600}>
                <RequiredFieldLabel label="Исходный договор и приложения" isValid={files.length > 0} />
              </Typography>

                <Stack direction="row" spacing={1} alignItems="center">
                <Box sx={{ color: 'primary.main', display: 'inline-flex', alignItems: 'center' }}>
                  <InfoOutlinedIcon fontSize="small" />
                </Box>
                <Typography variant="body1" lineHeight={1.3}>
                  Для каждого файла выберите видимость и необходимость выделения спецификации. Файлы с отметкой «Скрыть от контрагентов» доступны только сотрудникам с доступом к заявке.
                </Typography>
              </Stack>

              <Box
                onDragOver={(event) => {
                  event.preventDefault();
                  setIsDraggingFiles(true);
                }}
                onDragLeave={(event) => {
                  event.preventDefault();
                  const nextTarget = event.relatedTarget;
                  if (nextTarget instanceof Node && event.currentTarget.contains(nextTarget)) {
                    return;
                  }
                  setIsDraggingFiles(false);
                }}
                onDrop={handleDrop}
                sx={(theme: Theme) => ({
                  border: '1px dashed',
                  borderColor: isDraggingFiles ? 'primary.main' : alpha(theme.palette.text.primary, 0.14),
                  borderRadius: 1,
                  backgroundColor: isDraggingFiles ? alpha(theme.palette.primary.main, 0.05) : theme.palette.background.paper,
                  px: { xs: 2, sm: 3 },
                  py: { xs: 2.5, sm: 3 },
                  textAlign: 'center',
                  transition: theme.transitions.create(['border-color', 'background-color']),
                })}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  hidden
                  multiple
                  accept={ALLOWED_UPLOAD_FILE_INPUT_ACCEPT}
                  onChange={(event) => {
                    handleFilesAdded(Array.from(event.target.files ?? []));
                    event.target.value = '';
                  }}
                />

                <Stack spacing={0.75} alignItems="center">
                  <Box sx={{ color: 'text.disabled' }}>
                    <CloudUploadOutlinedIcon sx={{ fontSize: 36 }} />
                  </Box>

                  <Typography variant="subtitle1" fontWeight={700} lineHeight={1.2}>
                    Выберите файлы или перетащите сюда
                  </Typography>

                  <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 410, lineHeight: 1.35 }}>
                    Поддерживаются {ALLOWED_UPLOAD_FILE_TYPES_LABEL}, включая сканы. До 5 файлов, каждый до {MAX_UPLOAD_FILE_SIZE_MB} МБ, вместе до 15 МБ.
                  </Typography>

                  <Button
                    variant="outlined"
                    onClick={() => fileInputRef.current?.click()}
                    sx={{ minWidth: 148, borderRadius: 1, textTransform: 'none', px: 2.25, py: 0.65, fontWeight: 600 }}
                  >
                    Загрузить файл
                  </Button>
                </Stack>
              </Box>

              {files.length > 0 ? (
                <RequestUploadList files={files} hiddenKeys={hiddenFileKeys} extractionKeys={extractionKeys}
                  disabled={isLoadingReview || isSubmittingRequest}
                  onHiddenChange={(file, checked) => setValue('hiddenFileKeys', checked
                    ? [...hiddenFileKeys, getFileKey(file)] : hiddenFileKeys.filter((key) => key !== getFileKey(file)), { shouldDirty: true, shouldValidate: true })}
                  onExtractionChange={(file, checked) => setValue('extractionKeys', checked
                    ? [...extractionKeys, getFileKey(file)] : extractionKeys.filter((key) => key !== getFileKey(file)), { shouldDirty: true, shouldValidate: true })}
                  onRemove={(file) => updateFiles(files.filter((item) => getFileKey(item) !== getFileKey(file)))} />
              ) : null}

              {errors.files ? (
                <Typography variant="caption" color="error">
                  {errors.files.message}
                </Typography>
              ) : null}
              {errors.extractionKeys ? <Typography role="alert" variant="caption" color="error">{errors.extractionKeys.message}</Typography> : null}
            </Stack>

            <ToggleSection
              title="Скрыть от контрагентов"
              checked={hideFromContractorsEnabled}
              onChange={(_event, checked) => {
                setHideFromContractorsEnabled(checked);
                if (!checked) {
                  setValue('hiddenContractorIds', [], {
                    shouldDirty: true,
                    shouldTouch: true,
                    shouldValidate: true,
                  });
                }
              }}
              description="Выбранные контрагенты не смогут узнать о создании заявки или получить к ней доступ."
            >
              <Controller
                control={control}
                name="hiddenContractorIds"
                render={({ field }) => (
                  <Autocomplete
                    multiple
                    options={contractorOptions}
                    loading={isLoadingContractors}
                    value={hiddenContractors}
                    onChange={(_, value) => field.onChange(value.map((item) => item.user_id))}
                    isOptionEqualToValue={(option, value) => option.user_id === value.user_id}
                    getOptionLabel={getContractorOptionLabel}
                    popupIcon={<ExpandMoreIcon fontSize="small" />}
                    renderInput={(params) => <TextField {...params} placeholder="Начните вводить компанию, ФИО, email или логин" />}
                    renderTags={(value, getTagProps) =>
                      value.map((option, index) => {
                        const { key, ...tagProps } = getTagProps({ index });
                        return (
                          <Chip
                            key={key}
                            label={option.company_name || option.full_name || option.user_id}
                            {...tagProps}
                            variant="outlined"
                            sx={{
                              maxWidth: '100%',
                              borderRadius: 2,
                              backgroundColor: 'background.paper',
                              '& .MuiChip-label': {
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                              },
                            }}
                          />
                        );
                      })
                    }
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        borderRadius: 2,
                        backgroundColor: 'background.paper',
                        minHeight: 48,
                      },
                    }}
                  />
                )}
              />
            </ToggleSection>

            <ToggleSection
              title="Дополнительная рассылка на электронную почту"
              checked={additionalEmailsEnabled}
              onChange={(_event, checked) => {
                setAdditionalEmailsEnabled(checked);
                if (!checked) {
                  setValue('additionalEmails', [], {
                    shouldDirty: true,
                    shouldTouch: true,
                    shouldValidate: true,
                  });
                }
              }}
              description="Введите адреса электронной почты по одному или сразу несколько адресов через запятую."
            >
              <AdditionalEmailsField
                ref={additionalEmailsFieldRef}
                emails={additionalEmails}
                hideHeader
                addButtonVariant="icon"
                placeholder="name@example.com"
                helperText={errors.additionalEmails?.message ?? 'Можно добавить несколько адресов через запятую.'}
                onChange={(nextEmails) => {
                  setValue('additionalEmails', nextEmails, {
                    shouldDirty: true,
                    shouldTouch: true,
                    shouldValidate: true,
                  });
                }}
                textFieldSx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    backgroundColor: 'background.paper',
                  },
                }}
                containerSx={{ mt: 0 }}
              />
            </ToggleSection>

            <Button
              variant="contained"
              fullWidth
              type="submit"
              disabled={isSubmittingRequest || isLoadingReview || isSubmitBlocked}
              sx={{ borderRadius: 1, textTransform: 'none', py: 1.25, fontSize: 18, fontWeight: 700, boxShadow: 'none' }}
            >
              {isLoadingReview ? 'Подготовка проверки...' : 'Проверить и создать заявку'}
            </Button>

          </Stack>
        </Box>
      </DialogContent>
    </Dialog>
    {review ? <RequestEmailReviewDialog
      creating preview={review.preview} fontStyles={review.fontStyles} isPending={isSubmittingRequest} onCancel={closeReview} onConfirm={handleConfirmCreation}
      pendingHint={showSlowFileCheckHint ? 'Проверка тяжёлых файлов может занять пару минут. Пожалуйста, не закрывайте страницу.' : undefined}
      localFiles={[...getPublicSourceFiles(review.snapshot), ...(review.snapshot.specification ? [review.snapshot.specification.file] : [])]}
      summary={{
        id: review.snapshot.requestNumber.trim(), description: review.snapshot.description?.trim() || null,
        deadline: `${review.snapshot.deadlineAt}T23:59:59`, amount: normalizeAmountValue(review.snapshot.initialAmount),
        files: [
          ...actualNormativeFiles.filter((item) => item.id === review.snapshot.normativeFileId)
            .map((item) => ({ name: item.original_name, downloadUrl: item.download_url })),
          ...getPublicSourceFiles(review.snapshot).map((file) => ({ name: file.name, file })),
          ...(review.snapshot.specification ? [{ name: review.snapshot.specification.file.name, file: review.snapshot.specification.file }] : []),
        ],
        sourceFiles: review.snapshot.files.filter((file) => review.snapshot.hiddenFileKeys.includes(getFileKey(file))).map((file) => ({ name: file.name, file })),
        extractionFiles: review.snapshot.files.filter((file) => review.snapshot.extractionKeys.includes(getFileKey(file))).map((file) => file.name),
        specification: review.snapshot.specification,
        hiddenContractors: contractorOptions.filter((item) => review.snapshot.hiddenContractorIds.includes(item.user_id))
          .map((item) => item.company_name || item.full_name || item.user_id),
      }}
    /> : null}
    </>
  );
};


