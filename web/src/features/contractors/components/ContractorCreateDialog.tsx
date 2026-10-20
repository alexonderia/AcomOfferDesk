import { zodResolver } from '@hookform/resolvers/zod';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Controller } from 'react-hook-form';
import { z } from 'zod';
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
} from '@mui/material';
import { createManualContractor } from '@shared/api/users/createManualContractor';
import {
  getManualContractorDuplicates,
  type ManualContractorDuplicate,
} from '@shared/api/users/getManualContractorDuplicates';
import { RequiredFieldLabel } from '@shared/components/forms/RequiredFieldLabel';
import { ValidatedTextField } from '@shared/components/forms/ValidatedTextField';
import { useLiveValidatedForm } from '@shared/lib/forms';
import { formatRuPhone, isValidRuPhone } from '@shared/lib/phone';
import { useSystemToasts } from '@shared/ui/toasts';
import { sectionTitleSx } from '@shared/theme/sectionTitleSx';

type ContractorCreateDialogProps = {
  open: boolean;
  onClose: () => void;
  onCreated: () => Promise<void>;
};

const emailRegex = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

const schema = z.object({
  companyName: z
    .string()
    .trim()
    .min(1, 'Укажите наименование компании')
    .max(256, 'Не более 256 символов'),
  inn: z
    .string()
    .trim()
    .regex(/^\d{10}$|^\d{12}$/, 'ИНН должен содержать 10 или 12 цифр'),
  companyPhone: z
    .string()
    .trim()
    .refine((value) => isValidRuPhone(value), 'Некорректный номер телефона'),
  companyMail: z
    .string()
    .trim()
    .optional()
    .refine((value) => !value || emailRegex.test(value), 'Некорректный e-mail'),
  address: z.string().trim().max(256, 'Не более 256 символов').optional(),
  note: z.string().trim().max(1024, 'Не более 1024 символов').optional(),
});

type FormValues = z.infer<typeof schema>;

export const ContractorCreateDialog = ({ open, onClose, onCreated }: ContractorCreateDialogProps) => {
  const { showSuccessToast, showErrorToast } = useSystemToasts();
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [duplicates, setDuplicates] = useState<ManualContractorDuplicate[]>([]);
  const [duplicatesLoading, setDuplicatesLoading] = useState(false);
  const duplicateRequestRef = useRef(0);
  const defaultValues = useMemo<FormValues>(
    () => ({
      companyName: '',
      inn: '',
      companyPhone: '',
      companyMail: '',
      address: '',
      note: '',
    }),
    []
  );

  const {
    register,
    control,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting, touchedFields, dirtyFields, submitCount },
  } = useLiveValidatedForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues,
  });

  const companyNameValue = watch('companyName');
  const innValue = watch('inn');
  const companyPhoneValue = watch('companyPhone');
  const companyMailValue = watch('companyMail');
  const touchedMap = touchedFields as Partial<Record<keyof FormValues, unknown>>;
  const dirtyMap = dirtyFields as Partial<Record<keyof FormValues, unknown>>;
  const getFieldError = (field: keyof FormValues) => {
    const shouldShow = submitCount > 0 || Boolean(touchedMap[field]) || Boolean(dirtyMap[field]);
    const message = errors[field]?.message;
    if (!shouldShow || typeof message !== 'string') {
      return undefined;
    }
    return message;
  };
  const hasValue = (value: string | undefined) => Boolean(value?.trim());
  const isCompanyNameValid = hasValue(companyNameValue) && !errors.companyName;
  const isInnValid = hasValue(innValue) && !errors.inn;
  const isCompanyPhoneValid = hasValue(companyPhoneValue) && !errors.companyPhone;
  const hasDuplicateQuery = [companyNameValue, innValue, companyMailValue]
    .some((value) => (value?.trim().length ?? 0) >= 2);

  useEffect(() => {
    if (!open) {
      duplicateRequestRef.current += 1;
      setDuplicates([]);
      setDuplicatesLoading(false);
      return;
    }
    const query = {
      companyName: companyNameValue?.trim() ?? '',
      inn: innValue?.trim() ?? '',
      companyMail: companyMailValue?.trim() ?? '',
    };
    if (![query.companyName, query.inn, query.companyMail].some((value) => value.length >= 2)) {
      setDuplicates([]);
      setDuplicatesLoading(false);
      return;
    }
    const requestId = duplicateRequestRef.current + 1;
    duplicateRequestRef.current = requestId;
    setDuplicatesLoading(true);
    const timer = window.setTimeout(() => {
      void getManualContractorDuplicates(query)
        .then((items) => {
          if (duplicateRequestRef.current === requestId) setDuplicates(items);
        })
        .catch(() => {
          if (duplicateRequestRef.current === requestId) setDuplicates([]);
        })
        .finally(() => {
          if (duplicateRequestRef.current === requestId) setDuplicatesLoading(false);
        });
    }, 350);
    return () => window.clearTimeout(timer);
  }, [companyMailValue, companyNameValue, innValue, open]);

  useEffect(() => {
    if (!open) {
      reset(defaultValues);
      setSubmitError(null);
    }
  }, [defaultValues, open, reset]);

  const handleClose = () => {
    if (isSubmitting) {
      return;
    }
    reset(defaultValues);
    setSubmitError(null);
    onClose();
  };

  const handleCreate = async (values: FormValues) => {
    setSubmitError(null);
    try {
      const created = await createManualContractor({
        company_name: values.companyName.trim(),
        inn: values.inn.trim(),
        company_phone: values.companyPhone.trim(),
        company_mail: values.companyMail?.trim() || undefined,
        address: values.address?.trim() || undefined,
        note: values.note?.trim() || undefined,
      });
      if (created.outcome === 'duplicate_found' && created.duplicate) {
        const email = created.duplicate.companyMail ? `, e-mail: ${created.duplicate.companyMail}` : '';
        setSubmitError(`Найден существующий контрагент: ИНН ${created.duplicate.inn}, ${created.duplicate.companyName}${email}.`);
        return;
      }
      await onCreated();
      showSuccessToast(`Контрагент ${created.userId} создан`);
      handleClose();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Не удалось создать контрагента';
      setSubmitError(message);
      showErrorToast(message);
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="lg" fullWidth>
      <DialogTitle>Добавить контрагента</DialogTitle>
      <DialogContent sx={{ display: 'flex', gap: 3, alignItems: 'flex-start', flexWrap: { xs: 'wrap', md: 'nowrap' } }}>
        <Box sx={{ flex: 1, minWidth: 0 }}>
        <Stack
          spacing={2}
          mt={0.5}
          component="form"
          id="contractor-create-form"
          onSubmit={(event) => {
            event.preventDefault();
            void handleSubmit(handleCreate)();
          }}
        >
          <Box sx={sectionTitleSx}>
            Данные для регистрации
          </Box>
          <ValidatedTextField
            label={<RequiredFieldLabel label="Наименование компании" isValid={isCompanyNameValid} />}
            fieldName="companyName"
            registration={register('companyName')}
            error={Boolean(getFieldError('companyName'))}
            helperText={getFieldError('companyName')}
            fullWidth
          />
          <ValidatedTextField
            label={<RequiredFieldLabel label="ИНН" isValid={isInnValid} />}
            fieldName="inn"
            registration={register('inn')}
            error={Boolean(getFieldError('inn'))}
            helperText={getFieldError('inn')}
            fullWidth
          />
          <Controller
            control={control}
            name="companyPhone"
            render={({ field }) => (
              <ValidatedTextField
                label={<RequiredFieldLabel label="Телефон компании" isValid={isCompanyPhoneValid} />}
                fieldName="companyPhone"
                name={field.name}
                inputRef={field.ref}
                value={field.value ?? ''}
                onChange={(event) => {
                  field.onChange(formatRuPhone(event.target.value));
                }}
                onBlur={field.onBlur}
                error={Boolean(getFieldError('companyPhone'))}
                helperText={getFieldError('companyPhone')}
                fullWidth
              />
            )}
          />
          <ValidatedTextField
            label="E-mail компании"
            fieldName="companyMail"
            registration={register('companyMail')}
            error={Boolean(getFieldError('companyMail'))}
            helperText={getFieldError('companyMail')}
            fullWidth
          />
          <ValidatedTextField
            label="Адрес"
            fieldName="address"
            registration={register('address')}
            error={Boolean(getFieldError('address'))}
            helperText={getFieldError('address')}
            fullWidth
          />
          <ValidatedTextField
            label="Примечание"
            fieldName="note"
            registration={register('note')}
            error={Boolean(getFieldError('note'))}
            helperText={getFieldError('note')}
            multiline
            minRows={3}
            fullWidth
          />
          {submitError ? <Alert severity="error">{submitError}</Alert> : null}
        </Stack>
        </Box>
        {(hasDuplicateQuery || duplicatesLoading || duplicates.length > 0) ? <Box
          component="aside"
          sx={{
            width: { xs: '100%', md: 320 },
            flexShrink: 0,
            border: '1px solid',
            borderColor: duplicates.length ? 'warning.main' : 'divider',
            borderRadius: 2,
            p: 2,
            bgcolor: 'background.paper',
            position: { md: 'sticky' },
            top: 0,
          }}
        >
          <Box sx={{ fontWeight: 700, mb: 1 }}>Возможные дубликаты</Box>
          {duplicatesLoading ? <Box sx={{ color: 'text.secondary', fontSize: 14 }}>Проверяем введённые данные…</Box> : null}
          {!duplicatesLoading && duplicates.length === 0 ? (
            <Box sx={{ color: 'text.secondary', fontSize: 14 }}>
              {![companyNameValue, innValue, companyMailValue].some((value) => (value?.trim().length ?? 0) >= 2)
                ? 'Введите название, ИНН или e-mail.'
                : 'Совпадений не найдено.'}
            </Box>
          ) : null}
          <Stack spacing={1}>
            {duplicates.map((item) => (
              <Box key={item.userId} sx={{ borderTop: '1px solid', borderColor: 'divider', pt: 1 }}>
                <Box sx={{ fontWeight: 600, mb: 0.5 }}>{item.companyName || item.fullName || item.userId}</Box>
                <Stack spacing={0.2} sx={{ fontSize: 13, color: 'text.secondary' }}>
                  <Box>ID: {item.userId}</Box>
                  <Box>Статус: {item.status}</Box>
                  {item.fullName ? <Box>ФИО: {item.fullName}</Box> : null}
                  {item.phone ? <Box>Телефон: {item.phone}</Box> : null}
                  {item.mail ? <Box>Личный email: {item.mail}</Box> : null}
                  {item.companyName ? <Box>Компания: {item.companyName}</Box> : null}
                  {item.inn ? <Box>ИНН: {item.inn}</Box> : null}
                  {item.companyPhone ? <Box>Телефон компании: {item.companyPhone}</Box> : null}
                  {item.companyMail ? <Box sx={{ overflowWrap: 'anywhere' }}>Email компании: {item.companyMail}</Box> : null}
                  {item.address ? <Box>Адрес: {item.address}</Box> : null}
                  {item.note ? <Box>Примечание: {item.note}</Box> : null}
                  {item.createdAt ? <Box>Создан: {item.createdAt}</Box> : null}
                  {item.updatedAt ? <Box>Изменён: {item.updatedAt}</Box> : null}
                </Stack>
              </Box>
            ))}
          </Stack>
        </Box> : null}
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button variant="outlined" onClick={handleClose} disabled={isSubmitting}>
          Отмена
        </Button>
        <Button
          type="submit"
          form="contractor-create-form"
          variant="contained"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Сохранение...' : 'Добавить контрагента'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
