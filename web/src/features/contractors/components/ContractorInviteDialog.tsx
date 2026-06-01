import { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
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
  TextField,
  Typography,
} from '@mui/material';
import {
  inviteContractors,
  type InviteContractorsFailure,
} from '@shared/api/contractors/inviteContractors';
import { getNormativeFiles } from '@shared/api/normative/getNormativeFiles';
import type { NormativeFileItem } from '@shared/api/normative/types';
import { parseEmailList } from '@shared/lib/emailList';
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

export const ContractorInviteDialog = ({
  open,
  onClose,
}: ContractorInviteDialogProps) => {
  const { showErrorToast, showSuccessToast } = useSystemToasts();
  const [inputValue, setInputValue] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<InviteResult | null>(null);
  const [normativeFiles, setNormativeFiles] = useState<NormativeFileItem[]>([]);
  const [isLoadingNormativeFiles, setIsLoadingNormativeFiles] = useState(false);
  const [normativeFilesError, setNormativeFilesError] = useState<string | null>(null);
  const [selectedNormativeFileId, setSelectedNormativeFileId] = useState<number | null>(null);
  const parsed = useMemo(() => parseEmailList(inputValue), [inputValue]);
  const hasValidEmails = parsed.valid.length > 0;
  const hasNormativeSelection = selectedNormativeFileId !== null;

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
    if (!hasValidEmails) {
      showErrorToast('Добавьте хотя бы один корректный email');
      return;
    }

    setIsSubmitting(true);
    setResult(null);

    try {
      const response = await inviteContractors({
        emails: parsed.valid,
        normativeFileId: selectedNormativeFileId,
      });
      const nextResult: InviteResult = {
        sent: response.data.sent,
        failed: response.data.failed,
        invalid: response.data.invalid,
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

    setInputValue('');
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
          <Typography variant="body2" color="text.secondary">
            Можно ввести несколько адресов через запятую, пробел или с новой строки.
          </Typography>

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

          <TextField
            multiline
            minRows={5}
            value={inputValue}
            onChange={(event) => {
              setInputValue(event.target.value);
              if (result) {
                setResult(null);
              }
            }}
            placeholder="example1@company.com, example2@company.com"
            fullWidth
          />

          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Корректные адреса: {parsed.valid.length}
            </Typography>
            <Stack direction="row" flexWrap="wrap" gap={1}>
              {parsed.valid.map((email) => (
                <Chip key={email} label={email} color="success" variant="outlined" />
              ))}
            </Stack>
          </Box>

          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Некорректные адреса: {parsed.invalid.length}
            </Typography>
            <Stack direction="row" flexWrap="wrap" gap={1}>
              {parsed.invalid.map((email) => (
                <Chip key={email} label={email} color="error" variant="outlined" />
              ))}
            </Stack>
          </Box>

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
