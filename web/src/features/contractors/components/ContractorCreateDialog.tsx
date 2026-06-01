import { zodResolver } from '@hookform/resolvers/zod';
import { useEffect, useMemo, useState } from 'react';
import { Controller } from 'react-hook-form';
import { z } from 'zod';
import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
} from '@mui/material';
import { createManualContractor } from '@shared/api/users/createManualContractor';
import { ValidatedTextField } from '@shared/components/forms/ValidatedTextField';
import { useLiveValidatedForm } from '@shared/lib/forms';
import { formatRuPhone, isValidRuPhone } from '@shared/lib/phone';
import { useSystemToasts } from '@shared/ui/toasts';

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
    formState: { errors, isSubmitting },
  } = useLiveValidatedForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues,
  });

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
          <ValidatedTextField
            label="Наименование компании"
            fieldName="companyName"
            registration={register('companyName')}
            error={Boolean(errors.companyName)}
            helperText={errors.companyName?.message}
            fullWidth
          />
          <ValidatedTextField
            label="ИНН"
            fieldName="inn"
            registration={register('inn')}
            error={Boolean(errors.inn)}
            helperText={errors.inn?.message}
            fullWidth
          />
          <Controller
            control={control}
            name="companyPhone"
            render={({ field }) => (
              <ValidatedTextField
                label="Телефон компании"
                fieldName="companyPhone"
                name={field.name}
                inputRef={field.ref}
                value={field.value ?? ''}
                onChange={(event) => {
                  field.onChange(formatRuPhone(event.target.value));
                }}
                onBlur={field.onBlur}
                error={Boolean(errors.companyPhone)}
                helperText={errors.companyPhone?.message}
                fullWidth
              />
            )}
          />
          <ValidatedTextField
            label="E-mail компании"
            fieldName="companyMail"
            registration={register('companyMail')}
            error={Boolean(errors.companyMail)}
            helperText={errors.companyMail?.message}
            fullWidth
          />
          <ValidatedTextField
            label="Адрес"
            fieldName="address"
            registration={register('address')}
            error={Boolean(errors.address)}
            helperText={errors.address?.message}
            fullWidth
          />
          <ValidatedTextField
            label="Примечание"
            fieldName="note"
            registration={register('note')}
            error={Boolean(errors.note)}
            helperText={errors.note?.message}
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
