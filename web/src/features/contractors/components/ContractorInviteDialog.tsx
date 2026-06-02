import { useEffect, useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormHelperText,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Typography
} from '@mui/material';
import {
  inviteContractors,
  type InviteContractorsFailure
} from '@shared/api/contractors/inviteContractors';
import { getNormativeFiles } from '@shared/api/normative/getNormativeFiles';
import type { NormativeFileItem } from '@shared/api/normative/types';
import { AdditionalEmailsField, type AdditionalEmailsFieldHandle } from '@shared/components/AdditionalEmailsField';
import { useSystemToasts } from '@shared/ui/toasts';

type ContractorInviteDialogProps = {
  open: boolean;
  onClose: () => void;
};

type InviteResult = {
  sent: string[];
  failed: InviteContractorsFailure[];
  invalid: string[];
};

const PRESENTATION_FILE_PATTERN = /(презентац|presentation)/i;
const INVITATION_SUBJECT = 'Приглашение в AcomOfferDesk';
const INVITATION_PREVIEW_TEXT = [
  'AcomOfferDesk',
  '',
  'Вы приглашены к работе в системе AcomOfferDesk.',
  'Инструкция по получению доступа приложена к письму в виде презентации.',
  '',
  'Кнопка письма: «Перейти к системе»',
  'Ссылка для входа: [будет подставлена автоматически]',
  '',
  'Если удобнее, вы можете связаться с контактным лицом напрямую:',
  '[имя контактного лица]',
  'Тел. (MAX): [телефон]',
  'Эл. почта: [email]',
  '',
  'Вложение: выбранный нормативный документ'
].join('\n');

const resolveDefaultNormativeFileId = (items: NormativeFileItem[]): number | null => {
  const preferred = items.find((item) => PRESENTATION_FILE_PATTERN.test(item.original_name));
  if (preferred) {
    return preferred.id;
  }
  if (items.length > 0) {
    return items[0].id;
  }
  return null;
};

export const ContractorInviteDialog = ({ open, onClose }: ContractorInviteDialogProps) => {
  const { showErrorToast, showSuccessToast } = useSystemToasts();
  const additionalEmailsFieldRef = useRef<AdditionalEmailsFieldHandle | null>(null);
  const [emails, setEmails] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<InviteResult | null>(null);
  const [normativeFiles, setNormativeFiles] = useState<NormativeFileItem[]>([]);
  const [isLoadingNormativeFiles, setIsLoadingNormativeFiles] = useState(false);
  const [normativeFilesError, setNormativeFilesError] = useState<string | null>(null);
  const [selectedNormativeFileId, setSelectedNormativeFileId] = useState<number | null>(null);
  const hasValidEmails = emails.length > 0;
  const hasNormativeSelection = selectedNormativeFileId !== null;
  const selectedNormativeFile = normativeFiles.find((item) => item.id === selectedNormativeFileId) ?? null;
  const invitationPreview = INVITATION_PREVIEW_TEXT.replace(
    'Вложение: выбранный нормативный документ',
    `Вложение: ${selectedNormativeFile?.original_name ?? 'выбранный нормативный документ'}`
  );

  useEffect(() => {
    if (!open) {
      return;
    }

    let isMounted = true;
    const loadNormativeFiles = async () => {
      setIsLoadingNormativeFiles(true);
      setNormativeFilesError(null);
      try {
        const items = await getNormativeFiles('actual');
        if (!isMounted) {
          return;
        }
        setNormativeFiles(items);
        setSelectedNormativeFileId(resolveDefaultNormativeFileId(items));
      } catch (error) {
        if (!isMounted) {
          return;
        }
        setNormativeFiles([]);
        setSelectedNormativeFileId(null);
        setNormativeFilesError(
          error instanceof Error ? error.message : 'Не удалось загрузить нормативные документы'
        );
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
  }, [open]);

  const handleSubmit = async () => {
    if (selectedNormativeFileId === null) {
      showErrorToast('Выберите нормативный документ с презентацией');
      return;
    }
    const nextEmails = additionalEmailsFieldRef.current?.commitPendingInput();
    if (nextEmails === null) {
      return;
    }
    if (!nextEmails || nextEmails.length === 0) {
      showErrorToast('Добавьте хотя бы один корректный e-mail');
      return;
    }

    setIsSubmitting(true);
    setResult(null);

    try {
      const response = await inviteContractors({
        emails: nextEmails,
        normativeFileId: selectedNormativeFileId
      });
      const nextResult: InviteResult = {
        sent: response.data.sent,
        failed: response.data.failed,
        invalid: response.data.invalid
      };
      setResult(nextResult);

      if (nextResult.sent.length > 0) {
        showSuccessToast(`Приглашения отправлены: ${nextResult.sent.length}`);
      }

      if (nextResult.sent.length === 0 && (nextResult.failed.length > 0 || nextResult.invalid.length > 0)) {
        showErrorToast('Не удалось отправить приглашения: проверьте детали ниже');
      }
    } catch (error) {
      showErrorToast(error instanceof Error ? error.message : 'Не удалось отправить приглашения');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (isSubmitting) {
      return;
    }

    setEmails([]);
    setResult(null);
    setNormativeFiles([]);
    setNormativeFilesError(null);
    setSelectedNormativeFileId(null);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>Пригласить контрагента</DialogTitle>
      <DialogContent>
        <Stack spacing={2} mt={0.5}>
          <FormControl fullWidth error={Boolean(normativeFilesError)}>
            <InputLabel id="contractor-invite-normative-file-label">Презентация-инструкция</InputLabel>
            <Select
              labelId="contractor-invite-normative-file-label"
              label="Презентация-инструкция"
              value={selectedNormativeFileId ?? ''}
              disabled={isLoadingNormativeFiles || normativeFiles.length === 0}
              onChange={(event) => {
                const value = Number(event.target.value);
                setSelectedNormativeFileId(Number.isFinite(value) ? value : null);
              }}
            >
              {normativeFiles.map((item) => (
                <MenuItem key={item.id} value={item.id}>
                  {item.original_name}
                </MenuItem>
              ))}
            </Select>
            <FormHelperText>
              {isLoadingNormativeFiles
                ? 'Загружаем актуальные нормативные документы...'
                : normativeFiles.length === 0
                  ? 'Нет актуальных нормативных документов для вложения.'
                  : 'По умолчанию выбрана презентация, если она найдена в списке.'}
            </FormHelperText>
          </FormControl>

          {normativeFilesError ? <Alert severity="error">{normativeFilesError}</Alert> : null}

          <Box
            sx={(theme) => ({
              border: `1px solid ${theme.palette.divider}`,
              borderRadius: `${theme.acomShape.controlRadius}px`,
              backgroundColor: theme.palette.background.default,
              p: 2
            })}
          >
            <Stack spacing={0.75}>
              <Typography variant="subtitle2">Пример письма</Typography>
              <Typography variant="body2" color="text.secondary">
                Это шаблон письма, который получит контрагент.
              </Typography>
              <Typography variant="body2" fontWeight={600}>
                Тема: {INVITATION_SUBJECT}
              </Typography>
              <Box
                component="pre"
                sx={{
                  m: 0,
                  whiteSpace: 'pre-wrap',
                  fontFamily: 'inherit',
                  fontSize: 14,
                  lineHeight: 1.6,
                  color: 'text.primary'
                }}
              >
                {invitationPreview}
              </Box>
            </Stack>
          </Box>

          <AdditionalEmailsField
            ref={additionalEmailsFieldRef}
            emails={emails}
            onChange={(nextEmails) => {
              setEmails(nextEmails);
              if (result) {
                setResult(null);
              }
            }}
            hideHeader
            addButtonVariant="icon"
            placeholder="name@example.com"
            helperText="Можно ввести несколько адресов через запятую, пробел или с новой строки."
            disabled={isSubmitting}
            containerSx={{ mt: 0 }}
          />

          {result ? (
            <Alert severity={result.failed.length === 0 && result.invalid.length === 0 ? 'success' : 'info'}>
              Отправлено: {result.sent.length}. Ошибки: {result.failed.length}. Некорректные: {result.invalid.length}.
              {result.failed.length > 0 ? (
                <Box mt={1}>
                  {result.failed.map((item) => (
                    <Typography key={item.email} variant="body2">
                      {item.email}: {item.reason}
                    </Typography>
                  ))}
                </Box>
              ) : null}
              {result.invalid.length > 0 ? (
                <Box mt={1}>
                  <Typography variant="body2">
                    Некорректные email: {result.invalid.join(', ')}
                  </Typography>
                </Box>
              ) : null}
            </Alert>
          ) : null}
        </Stack>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button variant="outlined" onClick={handleClose} disabled={isSubmitting}>
          Отмена
        </Button>
        <Button
          variant="contained"
          onClick={() => void handleSubmit()}
          disabled={isSubmitting || !hasValidEmails || !hasNormativeSelection}
        >
          {isSubmitting ? 'Отправка...' : 'Отправить'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
