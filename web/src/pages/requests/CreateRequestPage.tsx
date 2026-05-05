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
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { alpha, type Theme } from '@mui/material/styles';
import { useEffect, useMemo, useRef, useState, type DragEvent } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { Navigate, useNavigate } from 'react-router-dom';
import { z } from 'zod';
import { useAuth } from '@app/providers/AuthProvider';
import { createRequest } from '@shared/api/requests/createRequest';
import { getRequestContractors, type RequestContractorItem } from '@shared/api/users/getRequestContractors';
import { hasPermission } from '@shared/auth/permissions';
import { AdditionalEmailsField, type AdditionalEmailsFieldHandle } from '@shared/components/AdditionalEmailsField';
import { DatePickerField } from '@shared/components/DatePickerField';
import { ToggleSection } from '@shared/components/ToggleSection';

const ALLOWED_FILE_EXTENSIONS = ['PDF', 'PNG', 'JPG', 'JPEG', 'TXT', 'MD', 'DOC', 'DOCX', 'DOCS', 'XLS', 'XLSX', 'EXL', 'CSV', 'ODS'];
const MAX_FILE_SIZE_MB = 10;
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
  initialAmount: z.string().trim().min(1, 'Укажите сумму по ТЗ').refine(isValidAmountValue, 'Укажите корректную сумму'),
  description: z.string().max(3000, 'Максимум 3000 символов').optional(),
  deadlineAt: z.string().min(1, 'Укажите дату завершения сбора откликов'),
  files: z.array(z.instanceof(File)).min(1, 'Добавьте хотя бы один файл'),
  additionalEmails: z.array(z.string().email('Введите корректный email')).default([]),
  hiddenContractorIds: z.array(z.string().min(1)).default([]),
});

type FormValues = z.infer<typeof schema>;

const getFileKey = (file: File) => `${file.name}-${file.size}-${file.lastModified}`;

const mergeUniqueFiles = (currentFiles: File[], addedFiles: File[]) => {
  const fileMap = new Map<string, File>();

  [...currentFiles, ...addedFiles].forEach((file) => {
    fileMap.set(getFileKey(file), file);
  });

  return Array.from(fileMap.values());
};

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

  const [isSubmittingRequest, setIsSubmittingRequest] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [contractorOptions, setContractorOptions] = useState<RequestContractorItem[]>([]);
  const [isLoadingContractors, setIsLoadingContractors] = useState(false);
  const [isDraggingFiles, setIsDraggingFiles] = useState(false);
  const [hideFromContractorsEnabled, setHideFromContractorsEnabled] = useState(false);
  const [additionalEmailsEnabled, setAdditionalEmailsEnabled] = useState(false);

  const {
    control,
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      initialAmount: '',
      description: '',
      deadlineAt: todayDate,
      files: [],
      additionalEmails: [],
      hiddenContractorIds: [],
    },
  });

  const files = watch('files');
  const additionalEmails = watch('additionalEmails');
  const hiddenContractorIds = watch('hiddenContractorIds');
  const hiddenContractors = useMemo(
    () => contractorOptions.filter((contractor) => hiddenContractorIds.includes(contractor.user_id)),
    [contractorOptions, hiddenContractorIds]
  );

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
          setErrorMessage(error instanceof Error ? error.message : 'Ошибка загрузки контрагентов');
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
  }, []);

  const updateFiles = (nextFiles: File[]) => {
    setValue('files', nextFiles, {
      shouldDirty: true,
      shouldTouch: true,
      shouldValidate: true,
    });
  };

  const handleFilesAdded = (addedFiles: File[]) => {
    updateFiles(mergeUniqueFiles(files, addedFiles));
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDraggingFiles(false);
    handleFilesAdded(Array.from(event.dataTransfer.files ?? []));
  };

  const handleSubmitForm = async (values: FormValues) => {
    const nextAdditionalEmails = additionalEmailsEnabled
      ? additionalEmailsFieldRef.current?.commitPendingInput()
      : [];

    if (nextAdditionalEmails === null) {
      return;
    }

    setIsSubmittingRequest(true);
    setErrorMessage(null);

    try {
      await createRequest({
        description: values.description?.trim() || null,
        deadline_at: `${values.deadlineAt}T23:59:59`,
        initial_amount: normalizeAmountValue(values.initialAmount),
        files: values.files,
        additional_emails: additionalEmailsEnabled ? nextAdditionalEmails ?? values.additionalEmails : [],
        hidden_contractor_ids: hideFromContractorsEnabled ? values.hiddenContractorIds : [],
      });
      navigate('/requests');
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Ошибка создания заявки');
    } finally {
      setIsSubmittingRequest(false);
    }
  };

  if (!canCreateRequest) {
    return <Navigate to="/requests" replace />;
  }

  return (
    <Dialog
      open
      onClose={() => navigate('/requests')}
      fullWidth
      maxWidth="sm"
      PaperProps={{
        sx: (theme: Theme) => ({
          borderRadius: 2,
          px: { xs: 2.5, sm: 3.5 },
          py: { xs: 3, sm: 3.5 },
          backgroundColor: theme.palette.background.default,
          maxHeight: 'min(760px, calc(100vh - 32px))',
          overflow: 'hidden',
          boxShadow: `0 24px 80px ${alpha(theme.palette.common.black, 0.18)}`,
        }),
      }}
    >
      <DialogContent
        sx={{
          p: 0,
          overflowX: 'hidden',
          overflowY: 'auto',
          scrollbarWidth: 'none',
          '&::-webkit-scrollbar': {
            display: 'none',
          },
        }}
      >
        <Box component="form" onSubmit={handleSubmit(handleSubmitForm)}>
          <Stack spacing={2}>
            <Typography variant="h5" fontWeight={600} lineHeight={1}>
              Новая заявка
            </Typography>

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
                  Дата завершения сбора откликов
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  (до 23:59)
                </Typography>
              </Box>
              <DatePickerField
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
                Сумма по ТЗ
              </Typography>
              <TextField
                placeholder="Укажите сумму в рублях"
                fullWidth
                error={Boolean(errors.initialAmount)}
                helperText={errors.initialAmount?.message ?? 'Значение «Сумма по ТЗ» используется для расчета экономии по заявке.'}
                {...register('initialAmount')}
                inputProps={{ min: 0, step: '0.01', inputMode: 'decimal' }}
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
                Загрузить документы
              </Typography>

                <Stack direction="row" spacing={1} alignItems="center">
                <Box sx={{ color: 'primary.main', display: 'inline-flex', alignItems: 'center' }}>
                  <InfoOutlinedIcon fontSize="small" />
                </Box>
                <Typography variant="body1" lineHeight={1.3}>
                  Карта партнера будет прикреплена к заявке автоматически.
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
                    Поддерживаются {ALLOWED_FILE_EXTENSIONS.join(', ')}. Размер одного файла до {MAX_FILE_SIZE_MB} МБ.
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
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {files.map((file) => (
                    <Chip
                      key={getFileKey(file)}
                      label={file.name}
                      onDelete={() => updateFiles(files.filter((item) => getFileKey(item) !== getFileKey(file)))}
                      variant="outlined"
                      sx={{
                        maxWidth: '100%',
                        borderRadius: 1,
                        backgroundColor: 'background.paper',
                        '& .MuiChip-label': {
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                        },
                      }}
                    />
                  ))}
                </Box>
              ) : null}

              {errors.files ? (
                <Typography variant="caption" color="error">
                  {errors.files.message}
                </Typography>
              ) : null}
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
              disabled={isSubmittingRequest}
              sx={{ borderRadius: 1, textTransform: 'none', py: 1.25, fontSize: 18, fontWeight: 700, boxShadow: 'none' }}
            >
              {isSubmittingRequest ? 'Создание...' : 'Создать заявку'}
            </Button>

            {errorMessage ? (
              <Typography color="error" textAlign="center">
                {errorMessage}
              </Typography>
            ) : null}
          </Stack>
        </Box>
      </DialogContent>
    </Dialog>
  );
};
