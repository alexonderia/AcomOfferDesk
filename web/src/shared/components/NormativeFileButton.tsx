import UploadFileOutlined from '@mui/icons-material/UploadFileOutlined';
import { Alert, Box, Button, Dialog, DialogContent, Stack, Tooltip, Typography } from '@mui/material';
import { alpha, type Theme, useTheme } from '@mui/material/styles';
import { useRef, useState } from 'react';
import { useAuth } from '@app/providers/AuthProvider';
import { uploadNormativeFile } from '@shared/api/normative/uploadNormativeFile';
import { ActionButton } from '@shared/components/ActionButton';
import { ROLE } from '@shared/constants/roles';
import { blurActiveElement } from '@shared/lib/dom/blurActiveElement';

const dialogPaperSx = (theme: Theme) => ({
  borderRadius: 2,
  px: { xs: 2.5, sm: 3.5 },
  py: { xs: 3, sm: 3.5 },
  backgroundColor: theme.palette.background.default,
  maxHeight: 'min(760px, calc(100vh - 32px))',
  overflow: 'hidden',
  boxShadow: `0 24px 80px ${alpha(theme.palette.common.black, 0.18)}`
});

const dialogContentSx = {
  p: 0,
  overflowX: 'hidden',
  overflowY: 'auto',
  scrollbarWidth: 'none',
  '&::-webkit-scrollbar': {
    display: 'none'
  }
};

type NormativeFileButtonProps = {
  iconOnly?: boolean;
  sidebar?: boolean;
};

export const NormativeFileButton = ({ iconOnly = false, sidebar = false }: NormativeFileButtonProps) => {
  const theme = useTheme();
  const { session } = useAuth();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [open, setOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (session?.roleId !== ROLE.LEAD_ECONOMIST) {
    return null;
  }

  const handleClose = () => {
    setOpen(false);
    setSelectedFile(null);
    setError(null);
    setSuccessMessage(null);
    setIsSubmitting(false);
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  };

  const handleOpen = () => {
    blurActiveElement();
    setOpen(true);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Выберите файл');
      return;
    }

    setIsSubmitting(true);
    setError(null);
    setSuccessMessage(null);
    try {
      await uploadNormativeFile(selectedFile, 1);
      setSuccessMessage('Нормативный документ загружен');
      setSelectedFile(null);
      if (inputRef.current) {
        inputRef.current.value = '';
      }
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : 'Не удалось загрузить нормативный документ');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      {sidebar ? (
        <Tooltip title="Нормативный документ" placement="right" enterDelay={150} disableHoverListener={!iconOnly}>
          <Box component="span" sx={{ display: 'block', width: '100%' }}>
            <ActionButton
              kind="custom"
              showNavigationIcons={false}
              onClick={handleOpen}
              aria-label="Загрузить нормативный документ"
              sx={{
                width: '100%',
                minHeight: iconOnly ? 42 : 52,
                minWidth: 0,
                borderRadius: `${theme.acomShape.buttonRadius}px !important`,
                justifyContent: iconOnly ? 'center' : 'flex-start',
                alignItems: iconOnly ? 'center' : 'flex-start',
                py: iconOnly ? 0 : 0.75,
                px: iconOnly ? 0 : 1.75,
                gap: iconOnly ? 0 : 1.25,
                transition: 'padding 0.32s ease, gap 0.32s ease'
              }}
            >
              <Box component="span" sx={{ display: 'inline-flex', lineHeight: 1 }}>
                <UploadFileOutlined fontSize="small" />
              </Box>
              <Stack spacing={0.15} sx={{ minWidth: 0, textAlign: 'left' }}>
                <Typography
                  sx={{
                    maxWidth: iconOnly ? 0 : 180,
                    opacity: iconOnly ? 0 : 1,
                    transform: iconOnly ? 'translateX(-4px)' : 'translateX(0)',
                    overflow: 'hidden',
                    textOverflow: 'clip',
                    whiteSpace: 'nowrap',
                    fontSize: 14,
                    fontWeight: 500,
                    lineHeight: 1.15,
                    transition: 'max-width 0.34s ease, opacity 0.24s ease, transform 0.34s ease'
                  }}
                >
                  Нормативный
                </Typography>
                <Typography
                  sx={{
                    maxWidth: iconOnly ? 0 : 180,
                    opacity: iconOnly ? 0 : 1,
                    transform: iconOnly ? 'translateX(-4px)' : 'translateX(0)',
                    overflow: 'hidden',
                    textOverflow: 'clip',
                    whiteSpace: 'nowrap',
                    fontSize: 14,
                    fontWeight: 500,
                    lineHeight: 1.15,
                    transition: 'max-width 0.34s ease, opacity 0.24s ease, transform 0.34s ease'
                  }}
                >
                  документ
                </Typography>
              </Stack>
            </ActionButton>
          </Box>
        </Tooltip>
      ) : iconOnly ? (
        <Tooltip title="Нормативный документ" placement="right">
          <Box component="span" sx={{ display: 'block', width: '100%' }}>
            <ActionButton
              kind="custom"
              showNavigationIcons={false}
              onClick={handleOpen}
              aria-label="Загрузить нормативный документ"
              sx={{
                width: '100%',
                minHeight: 42,
                minWidth: 0,
                borderRadius: `${theme.acomShape.buttonRadius}px !important`,
                justifyContent: 'center',
                px: 0,
                gap: 0,
              }}
            >
              <Box component="span" sx={{ display: 'inline-flex', lineHeight: 1 }}>
                <UploadFileOutlined fontSize="small" />
              </Box>
            </ActionButton>
          </Box>
        </Tooltip>
      ) : (
        <Button
          variant="outlined"
          onClick={handleOpen}
          sx={{ borderRadius: 999, textTransform: 'none', px: 3, whiteSpace: 'nowrap' }}
        >
          Добавить нормативный документ
        </Button>
      )}
      <Dialog
        open={open}
        onClose={handleClose}
        fullWidth
        maxWidth="sm"
        PaperProps={{ sx: dialogPaperSx }}
      >
        <DialogContent sx={dialogContentSx}>
          <Stack spacing={2}>
            <Typography variant="h5" fontWeight={600} lineHeight={1}>
              Загрузка нормативного документа
            </Typography>

            <Typography variant="body2" color="text.secondary">
              Загруженный файл используется системой при создании заявок для автоматического прикрепления карты партнера.
            </Typography>
            <Typography variant="body2" color="warning.main">
              Важно: нормативный документ можно загрузить только один раз.
            </Typography>

            {error ? <Alert severity="error">{error}</Alert> : null}
            {successMessage ? <Alert severity="success">{successMessage}</Alert> : null}

            <Box
              sx={{
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: 1,
                p: { xs: 1.5, sm: 1.8 },
                backgroundColor: 'background.paper'
              }}
            >
              <Stack spacing={1.2}>
                <input
                  ref={inputRef}
                  type="file"
                  hidden
                  onChange={(event) => {
                    setSelectedFile(event.target.files?.[0] ?? null);
                    setError(null);
                    setSuccessMessage(null);
                  }}
                />
                <Button
                  variant="outlined"
                  onClick={() => inputRef.current?.click()}
                  disabled={isSubmitting}
                  sx={{ width: 'fit-content', borderRadius: 1, textTransform: 'none' }}
                >
                  Выбрать файл
                </Button>
                <Typography variant="body2" color="text.secondary">
                  {selectedFile ? `Выбран файл: ${selectedFile.name}` : 'Файл не выбран. После успешной загрузки повторная загрузка будет недоступна.'}
                </Typography>
              </Stack>
            </Box>

            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
              <Button
                variant="outlined"
                onClick={handleClose}
                disabled={isSubmitting}
                sx={{ borderRadius: 1, textTransform: 'none', py: 1.1 }}
              >
                Отмена
              </Button>
              <Button
                onClick={() => void handleUpload()}
                variant="contained"
                fullWidth
                disabled={isSubmitting}
                sx={{ borderRadius: 1, textTransform: 'none', py: 1.1, fontSize: 16, fontWeight: 700, boxShadow: 'none' }}
              >
                {isSubmitting ? 'Загружаем...' : 'Загрузить документ'}
              </Button>
            </Stack>
          </Stack>
        </DialogContent>
      </Dialog>
    </>
  );
};
