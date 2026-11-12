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
import { inviteContractors } from '@shared/api/contractors/inviteContractors';
import { getNormativeFiles } from '@shared/api/normative/getNormativeFiles';
import type { NormativeFileItem } from '@shared/api/normative/types';
import { AdditionalEmailsField, type AdditionalEmailsFieldHandle } from '@shared/components/AdditionalEmailsField';
import { RequiredFieldLabel } from '@shared/components/forms/RequiredFieldLabel';
import { useSystemToasts } from '@shared/ui/toasts';
import fontStyles from '../../../../../shared/fonts/alabuga-sans.css?inline';

type ContractorInviteDialogProps = {
  open: boolean;
  onClose: () => void;
};

const PRESENTATION_FILE_PATTERN = /(презентац|presentation)/i;
const INVITATION_SUBJECT = 'Приглашение в AcomOfferDesk';
const PREVIEW_PORTAL_URL = 'https://acomofferdesk.example.com';
const PREVIEW_CONTACT_NAME = 'Владислав Хлистун';
const PREVIEW_CONTACT_PHONE = '+7 927 455-80-89';
const PREVIEW_CONTACT_EMAIL = 'VKhlistun@alabuga.ru';

const INVITATION_PREVIEW_HTML = `<!DOCTYPE html>
<html lang="ru">
  <head>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <style>
      ${fontStyles}
      body{overflow-wrap:anywhere}
      @media(max-width:480px){
        table[width="600"]>tbody>tr>td{padding-left:12px!important;padding-right:12px!important}
        table[width="600"]>tbody>tr:first-child>td{font-size:18px!important}
      }
    </style>
  </head>
  <body style="margin:0;padding:0;background-color:#f6f8fb;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color:#f6f8fb;padding:24px 12px;">
      <tr>
        <td align="center">
          <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="600" style="width:100%;max-width:600px;background:#ffffff;border:1px solid #e6e8eb;border-radius:10px;">
            <tr>
              <td style="padding:24px 28px 8px 28px;font-family:'Alabuga Sans',sans-serif;color:#111827;font-size:22px;font-weight:700;">
                AcomOfferDesk
              </td>
            </tr>
            <tr>
              <td style="padding:0 28px;font-family:'Alabuga Sans',sans-serif;color:#111827;font-size:16px;line-height:24px;">
                Вы приглашены к работе в системе AcomOfferDesk.<br/><br/>
                Инструкция по получению доступа приложена к письму в виде презентации.
              </td>
            </tr>
            <tr>
              <td style="padding:24px 28px 8px 28px;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                  <tr>
                    <td bgcolor="#0969da" style="border-radius:6px;">
                      <span style="display:inline-block;padding:12px 20px;font-family:'Alabuga Sans',sans-serif;font-size:16px;color:#ffffff;text-decoration:none;cursor:default;">
                        Перейти к системе
                      </span>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="padding:16px 28px 0 28px;font-family:'Alabuga Sans',sans-serif;color:#374151;font-size:14px;line-height:22px;">
                Если удобнее, вы можете связаться с контактным лицом напрямую:<br/>
                <strong>${PREVIEW_CONTACT_NAME}</strong><br/>
                Телефон: ${PREVIEW_CONTACT_PHONE}<br/>
                Эл. почта: ${PREVIEW_CONTACT_EMAIL}
              </td>
            </tr>
            <tr>
              <td style="padding:8px 28px 24px 28px;font-family:'Alabuga Sans',sans-serif;color:#374151;font-size:14px;line-height:22px;">
                Ссылка для входа:<br/>
                ${PREVIEW_PORTAL_URL}
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>`;

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
  const previewFrameRef = useRef<HTMLIFrameElement | null>(null);
  const previewResizeObserverRef = useRef<ResizeObserver | null>(null);
  const [emails, setEmails] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [normativeFiles, setNormativeFiles] = useState<NormativeFileItem[]>([]);
  const [isLoadingNormativeFiles, setIsLoadingNormativeFiles] = useState(false);
  const [normativeFilesError, setNormativeFilesError] = useState<string | null>(null);
  const [selectedNormativeFileId, setSelectedNormativeFileId] = useState<number | null>(null);
  const [previewFrameHeight, setPreviewFrameHeight] = useState<number | null>(null);
  const hasValidEmails = emails.length > 0;
  const hasNormativeSelection = selectedNormativeFileId !== null;

  const syncPreviewFrameHeight = () => {
    const frame = previewFrameRef.current;
    const frameDocument = frame?.contentWindow?.document;
    if (!frameDocument) {
      return;
    }

    const borderHeight = (frame?.offsetHeight ?? 0) - (frame?.clientHeight ?? 0);
    const nextHeight = Math.ceil(frameDocument.body?.getBoundingClientRect().height ?? 0) + borderHeight;
    if (nextHeight > 0) {
      setPreviewFrameHeight(nextHeight);
    }
  };

  useEffect(() => {
    if (!open) {
      setPreviewFrameHeight(null);
    }
    return () => previewResizeObserverRef.current?.disconnect();
  }, [open]);

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

    try {
      const response = await inviteContractors({
        emails: nextEmails,
        normativeFileId: selectedNormativeFileId
      });
      const sentCount = response.data.sent.length;
      const failedCount = response.data.failed.length;
      const invalidCount = response.data.invalid.length;

      if (sentCount > 0) {
        showSuccessToast(`Приглашения отправлены: ${sentCount}`);
      }

      if (sentCount === 0 && (failedCount > 0 || invalidCount > 0)) {
        showErrorToast('Не удалось отправить приглашения. Проверьте детали в центре уведомлений.');
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
            <InputLabel id="contractor-invite-normative-file-label"><RequiredFieldLabel label="Презентация-инструкция" isValid={hasNormativeSelection} /></InputLabel>
            <Select
              labelId="contractor-invite-normative-file-label"
              label={<RequiredFieldLabel label="Презентация-инструкция" isValid={hasNormativeSelection} />}
              inputProps={{ 'aria-required': true }}
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
              <Typography variant="body2" fontWeight={600}>
                Тема: {INVITATION_SUBJECT}
              </Typography>
              <Box
                component="iframe"
                title="Предпросмотр письма"
                sandbox="allow-same-origin"
                ref={previewFrameRef}
                srcDoc={INVITATION_PREVIEW_HTML}
                scrolling="no"
                onLoad={() => {
                  previewResizeObserverRef.current?.disconnect();
                  const frameDocument = previewFrameRef.current?.contentDocument;
                  if (frameDocument?.body && typeof ResizeObserver !== 'undefined') {
                    const observer = new ResizeObserver(syncPreviewFrameHeight);
                    observer.observe(frameDocument.body);
                    previewResizeObserverRef.current = observer;
                  }
                  syncPreviewFrameHeight();
                  void frameDocument?.fonts?.ready.then(syncPreviewFrameHeight);
                }}
                sx={{
                  display: 'block',
                  width: '100%',
                  height: previewFrameHeight ? `${previewFrameHeight}px` : undefined,
                  minHeight: previewFrameHeight ? undefined : { xs: 520, sm: 440 },
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 1.5,
                  backgroundColor: 'common.white'
                }}
              />
            </Stack>
          </Box>

          <AdditionalEmailsField
            required
            label="E-mail получателей"
            ref={additionalEmailsFieldRef}
            emails={emails}
            onChange={(nextEmails) => {
              setEmails(nextEmails);
            }}
            hideHeader
            addButtonVariant="icon"
            placeholder="name@example.com"
            helperText="Можно ввести несколько адресов через запятую, пробел или с новой строки."
            disabled={isSubmitting}
            containerSx={{ mt: 0 }}
          />

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
