import { zodResolver } from '@hookform/resolvers/zod';
import { useEffect, useMemo, useState } from 'react';
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
import { RequiredFieldLabel } from '@shared/components/forms/RequiredFieldLabel';
import { ValidatedTextField } from '@shared/components/forms/ValidatedTextField';
import { useLiveValidatedForm } from '@shared/lib/forms';
import { formatRuPhone, isValidRuPhone } from '@shared/lib/phone';
import { useSystemToasts } from '@shared/ui/toasts';
import { sectionTitleSx } from '@shared/theme/sectionTitleSx';
import { InitialAccountFields, type InitialAccountValues } from '@shared/components/InitialAccountFields';
import { normalizeOptionalContractorValue } from '@shared/lib/manualContractorEditing';
import { ManualContractorDuplicatePanel } from './ManualContractorDuplicatePanel';

type ContractorCreateDialogProps = {
  open: boolean;
  onClose: () => void;
  onCreated: () => Promise<void>;
  emailEnabled?: boolean;
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

export const ContractorCreateDialog = ({ open, onClose, onCreated, emailEnabled = true }: ContractorCreateDialogProps) => {
  const [account, setAccount] = useState<InitialAccountValues>({ login: '', password: '', password_confirmation: '' });
  const [existingUserId, setExistingUserId] = useState<string | undefined>();
  const { showSuccessToast, showErrorToast } = useSystemToasts();
  const [submitError, setSubmitError] = useState<string | null>(null);
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
  const addressValue = watch('address');
  const noteValue = watch('note');
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

  useEffect(() => {
    if (!open) {
      reset(defaultValues);
      setAccount({ login: '', password: '', password_confirmation: '' });
      setExistingUserId(undefined);
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
        existing_user_id: existingUserId,
        ...(!emailEnabled && (account.login || account.password || account.password_confirmation) ? { login: account.login.trim(), password: account.password, password_confirmation: account.password_confirmation } : {}),
      });
      await onCreated();
      showSuccessToast(created.outcome === 'duplicate_found' ? `Использован существующий контрагент ${created.userId}` : `Контрагент ${created.userId} создан`);
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
            value={companyNameValue ?? ''}
            error={Boolean(getFieldError('companyName'))}
            helperText={getFieldError('companyName')}
            fullWidth
          />
          <ValidatedTextField
            label={<RequiredFieldLabel label="ИНН" isValid={isInnValid} />}
            fieldName="inn"
            registration={register('inn')}
            value={innValue ?? ''}
            inputProps={{ inputMode: 'numeric', maxLength: 12 }}
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
            value={companyMailValue ?? ''}
            error={Boolean(getFieldError('companyMail'))}
            helperText={getFieldError('companyMail')}
            fullWidth
          />
          <ValidatedTextField
            label="Адрес"
            fieldName="address"
            registration={register('address')}
            value={addressValue ?? ''}
            error={Boolean(getFieldError('address'))}
            helperText={getFieldError('address')}
            fullWidth
          />
          <ValidatedTextField
            label="Примечание"
            fieldName="note"
            registration={register('note')}
            value={noteValue ?? ''}
            error={Boolean(getFieldError('note'))}
            helperText={getFieldError('note')}
            multiline
            minRows={3}
            fullWidth
          />
          {submitError ? <Alert severity="error">{submitError}</Alert> : null}
          {!emailEnabled ? <InitialAccountFields values={account} onChange={(field, value) => setAccount((old) => ({ ...old, [field]: value }))} disabled={isSubmitting} /> : null}
        </Stack>
        </Box>
        <ManualContractorDuplicatePanel
          open={open} companyName={companyNameValue} inn={innValue} companyMail={companyMailValue}
          disabled={isSubmitting}
          onSelect={(item) => {
            setExistingUserId(item.userId);
            setAccount({ login: '', password: '', password_confirmation: '' });
            reset({
              companyName: normalizeOptionalContractorValue(item.companyName),
              inn: normalizeOptionalContractorValue(item.inn),
              companyPhone: normalizeOptionalContractorValue(item.companyPhone),
              companyMail: normalizeOptionalContractorValue(item.companyMail),
              address: normalizeOptionalContractorValue(item.address),
              note: normalizeOptionalContractorValue(item.note),
            });
          }}
        />
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
