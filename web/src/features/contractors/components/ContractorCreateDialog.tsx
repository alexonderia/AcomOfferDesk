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
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Добавить контрагента</DialogTitle>
      <DialogContent>
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
