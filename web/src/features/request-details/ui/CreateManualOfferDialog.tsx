import { useEffect, useMemo, useRef, useState, type DragEvent } from 'react';
import CloudUploadOutlinedIcon from '@mui/icons-material/CloudUploadOutlined';
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Chip,
  Dialog,
  DialogContent,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography
} from '@mui/material';
import { alpha, type Theme } from '@mui/material/styles';
import { createManualOfferForRequest } from '@shared/api/offers/createManualOfferForRequest';
import { getRequestContractors, type RequestContractorItem } from '@shared/api/users/getRequestContractors';
import { getFileKey } from '@shared/lib/files';
import { formatRuPhone, isValidRuPhone } from '@shared/lib/phone';

type Props = {
  open: boolean;
  requestId: number;
  onClose: () => void;
  onCreated: (workspacePath: string) => void;
};

type ContractorMode = 'existing' | 'new';

const getContractorOptionLabel = (contractor: RequestContractorItem) => {
  const primary = contractor.company_name?.trim() || contractor.full_name?.trim() || contractor.user_id;
  const secondary = contractor.company_mail?.trim() || contractor.mail?.trim() || contractor.user_id;
  return `${primary} (${secondary})`;
};

const parseAmount = (value: string) => {
  const normalized = value.trim().replace(',', '.');
  if (!normalized) {
    return null;
  }
  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : Number.NaN;
};

const emailRegex = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export const CreateManualOfferDialog = ({ open, requestId, onClose, onCreated }: Props) => {
  const [contractorMode, setContractorMode] = useState<ContractorMode>('existing');
  const [contractorOptions, setContractorOptions] = useState<RequestContractorItem[]>([]);
  const [selectedContractor, setSelectedContractor] = useState<RequestContractorItem | null>(null);

  const [companyName, setCompanyName] = useState('');
  const [inn, setInn] = useState('');
  const [companyPhone, setCompanyPhone] = useState('');
  const [companyMail, setCompanyMail] = useState('');
  const [address, setAddress] = useState('');
  const [note, setNote] = useState('');
  const [offerAmount, setOfferAmount] = useState('');

  const [files, setFiles] = useState<File[]>([]);
  const [isDraggingFiles, setIsDraggingFiles] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [isLoadingContractors, setIsLoadingContractors] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitAttempted, setIsSubmitAttempted] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!open) {
      return;
    }
    let isMounted = true;
    setIsLoadingContractors(true);
    getRequestContractors()
      .then((response) => {
        if (!isMounted) {
          return;
        }
        setContractorOptions(response.items);
      })
      .catch((error) => {
        if (isMounted) {
          setErrorMessage(error instanceof Error ? error.message : 'Не удалось загрузить контрагентов');
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsLoadingContractors(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [open]);

  const resetForm = () => {
    setContractorMode('existing');
    setSelectedContractor(null);
    setCompanyName('');
    setInn('');
    setCompanyPhone('');
    setCompanyMail('');
    setAddress('');
    setNote('');
    setOfferAmount('');
    setFiles([]);
    setIsSubmitAttempted(false);
    setErrorMessage(null);
  };

  const handleClose = () => {
    if (isSubmitting) {
      return;
    }
    resetForm();
    onClose();
  };

  const parsedAmount = useMemo(() => parseAmount(offerAmount), [offerAmount]);
  const trimmedCompanyName = companyName.trim();
  const trimmedInn = inn.trim();
  const trimmedCompanyPhone = companyPhone.trim();
  const trimmedCompanyMail = companyMail.trim();
  const trimmedAddress = address.trim();
  const trimmedNote = note.trim();
  const isAmountInvalid =
    offerAmount.trim().length > 0
    && (Number.isNaN(parsedAmount) || (parsedAmount !== null && parsedAmount < 0));

  const companyNameError = contractorMode === 'new'
    ? (
        (isSubmitAttempted && !trimmedCompanyName)
          ? 'Наименование компании обязательно'
          : (trimmedCompanyName.length > 256 ? 'Наименование компании не должно превышать 256 символов' : null)
      )
    : null;
  const innError = contractorMode === 'new'
    ? (
        (isSubmitAttempted && !trimmedInn)
          ? 'ИНН обязателен'
          : (trimmedInn && !/^\d{10}$|^\d{12}$/.test(trimmedInn) ? 'ИНН должен содержать 10 или 12 цифр' : null)
      )
    : null;
  const companyPhoneError = contractorMode === 'new'
    ? (
        (isSubmitAttempted && !trimmedCompanyPhone)
          ? 'Телефон компании обязателен'
          : (trimmedCompanyPhone && !isValidRuPhone(trimmedCompanyPhone) ? 'Некорректный формат телефона компании' : null)
      )
    : null;
  const companyMailError = trimmedCompanyMail && !emailRegex.test(trimmedCompanyMail)
    ? 'Некорректный формат e-mail компании'
    : null;
  const addressError = trimmedAddress.length > 256 ? 'Адрес не должен превышать 256 символов' : null;
  const noteError = trimmedNote.length > 1024 ? 'Дополнительная информация не должна превышать 1024 символа' : null;
  const amountError = isAmountInvalid
    ? (Number.isNaN(parsedAmount) ? 'Укажите корректную сумму КП' : 'Сумма КП не может быть отрицательной')
    : null;

  const canSubmit = useMemo(() => {
    if (isSubmitting) {
      return false;
    }
    if (isAmountInvalid) {
      return false;
    }
    if (contractorMode === 'existing') {
      return Boolean(selectedContractor);
    }
    return Boolean(
      trimmedCompanyName
      && trimmedInn
      && trimmedCompanyPhone
      && !companyNameError
      && !innError
      && !companyPhoneError
      && !companyMailError
      && !addressError
      && !noteError
    );
  }, [
    addressError,
    companyMailError,
    companyNameError,
    companyPhoneError,
    contractorMode,
    innError,
    isAmountInvalid,
    isSubmitting,
    noteError,
    selectedContractor,
    trimmedCompanyName,
    trimmedCompanyPhone,
    trimmedInn
  ]);

  const submitBlockReason = useMemo(() => {
    if (contractorMode === 'existing' && !selectedContractor) {
      return 'Выберите контрагента';
    }
    return companyNameError
      || innError
      || companyPhoneError
      || companyMailError
      || addressError
      || noteError
      || amountError
      || null;
  }, [
    addressError,
    amountError,
    companyMailError,
    companyNameError,
    companyPhoneError,
    contractorMode,
    innError,
    noteError,
    selectedContractor
  ]);

  const handleFilesAdded = (nextFiles: File[]) => {
    const map = new Map<string, File>();
    for (const file of [...files, ...nextFiles]) {
      map.set(getFileKey(file), file);
    }
    setFiles(Array.from(map.values()));
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDraggingFiles(false);
    handleFilesAdded(Array.from(event.dataTransfer.files ?? []));
  };

  const handleSubmit = async () => {
    setIsSubmitAttempted(true);
    setErrorMessage(null);
    if (!canSubmit) {
      setErrorMessage(submitBlockReason ?? 'Проверьте условия создания КП');
      return;
    }

    setIsSubmitting(true);
    try {
      const result = await createManualOfferForRequest(
        requestId,
        contractorMode === 'existing'
          ? {
              contractor_mode: 'existing',
              contractor_user_id: selectedContractor?.user_id ?? '',
              offer_amount: parsedAmount,
              files
            }
          : {
              contractor_mode: 'new',
              company_name: companyName.trim(),
              inn: inn.trim(),
              company_phone: companyPhone.trim(),
              company_mail: companyMail.trim() || undefined,
              address: address.trim() || undefined,
              note: note.trim() || undefined,
              offer_amount: parsedAmount,
              files
            }
      );
      resetForm();
      onCreated(result.workspacePath);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Не удалось создать КП вручную');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: (theme: Theme) => ({
          borderRadius: 2,
          px: { xs: 2.5, sm: 3.5 },
          py: { xs: 3, sm: 3.5 },
          backgroundColor: theme.palette.background.default,
          maxHeight: 'min(760px, calc(100vh - 32px))',
          overflow: 'hidden',
          boxShadow: `0 24px 80px ${alpha(theme.palette.common.black, 0.18)}`
        })
      }}
    >
      <DialogContent
        sx={{
          p: 0,
          overflowX: 'hidden',
          overflowY: 'auto',
          scrollbarWidth: 'none',
          '&::-webkit-scrollbar': {
            display: 'none'
          }
        }}
      >
        <Stack spacing={1.5}>
          <Typography variant="h5" fontWeight={600} lineHeight={1}>
            Ручное внесение КП
          </Typography>

          <Stack spacing={0.75}>
            <Typography variant="subtitle1" fontWeight={600}>
              Контрагент
            </Typography>
            <Select
              size="small"
              value={contractorMode}
              onChange={(event) => {
                setContractorMode(event.target.value as ContractorMode);
                setErrorMessage(null);
              }}
              sx={{ '& .MuiOutlinedInput-root': { borderRadius: 1 } }}
            >
              <MenuItem value="existing">Выбрать из списка</MenuItem>
              <MenuItem value="new">Создать нового</MenuItem>
            </Select>
          </Stack>

          {contractorMode === 'existing' ? (
            <Autocomplete
              options={contractorOptions}
              loading={isLoadingContractors}
              value={selectedContractor}
              onChange={(_, value) => setSelectedContractor(value)}
              isOptionEqualToValue={(option, value) => option.user_id === value.user_id}
              getOptionLabel={getContractorOptionLabel}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Выберите контрагента"
                  placeholder="Компания, ФИО, email или логин"
                />
              )}
            />
          ) : (
            <Stack spacing={0.75}>
              <TextField
                label="Наименование компании"
                value={companyName}
                onChange={(event) => setCompanyName(event.target.value)}
                error={Boolean(companyNameError)}
                helperText={companyNameError ?? undefined}
              />
              <TextField
                label="ИНН"
                value={inn}
                onChange={(event) => setInn(event.target.value)}
                error={Boolean(innError)}
                helperText={innError ?? undefined}
              />
              <TextField
                label="Телефон компании"
                value={companyPhone}
                onChange={(event) => setCompanyPhone(formatRuPhone(event.target.value))}
                placeholder="+7 (900) 999-88-77"
                error={Boolean(companyPhoneError)}
                helperText={companyPhoneError ?? undefined}
              />
              <TextField
                label="E-mail компании"
                value={companyMail}
                onChange={(event) => setCompanyMail(event.target.value)}
                error={Boolean(companyMailError)}
                helperText={companyMailError ?? undefined}
              />
              <TextField
                label="Адрес"
                value={address}
                onChange={(event) => setAddress(event.target.value)}
                error={Boolean(addressError)}
                helperText={addressError ?? undefined}
              />
              <TextField
                label="Дополнительная информация"
                value={note}
                onChange={(event) => setNote(event.target.value)}
                multiline
                minRows={2}
                error={Boolean(noteError)}
                helperText={noteError ?? undefined}
              />
            </Stack>
          )}

          <TextField
            label="Сумма КП, руб. (необязательно)"
            value={offerAmount}
            onChange={(event) => setOfferAmount(event.target.value)}
            inputProps={{ min: 0, step: '0.01', inputMode: 'decimal' }}
            error={Boolean(amountError)}
            helperText={amountError ?? undefined}
          />

          <Stack spacing={0.75}>
            <Typography variant="subtitle1" fontWeight={600}>
              Документы КП
            </Typography>
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
                px: 3,
                py: 2.5,
                textAlign: 'center',
                transition: theme.transitions.create(['border-color', 'background-color'])
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
                <CloudUploadOutlinedIcon sx={{ fontSize: 34, color: 'text.disabled' }} />
                <Typography variant="body2">Перетащите файлы сюда или загрузите вручную</Typography>
                <Button variant="outlined" onClick={() => fileInputRef.current?.click()}>
                  Загрузить файлы
                </Button>
              </Stack>
            </Box>
            {files.length > 0 ? (
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {files.map((file) => (
                  <Chip
                    key={getFileKey(file)}
                    label={file.name}
                    variant="outlined"
                    onDelete={() => setFiles((prev) => prev.filter((item) => getFileKey(item) !== getFileKey(file)))}
                  />
                ))}
              </Box>
            ) : null}
          </Stack>

          {errorMessage ? <Alert severity="error">{errorMessage}</Alert> : null}

          <Stack direction="row" spacing={1} justifyContent="flex-end">
            <Button variant="outlined" onClick={handleClose} disabled={isSubmitting}>
              Отмена
            </Button>
            <Button variant="contained" onClick={() => void handleSubmit()} disabled={!canSubmit}>
              {isSubmitting ? 'Создание...' : 'Создать КП'}
            </Button>
          </Stack>
        </Stack>
      </DialogContent>
    </Dialog>
  );
};
