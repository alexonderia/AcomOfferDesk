import FeedbackOutlined from '@mui/icons-material/FeedbackOutlined';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogContent,
  Stack,
  TextField,
  Tooltip,
  Typography
} from '@mui/material';
import { alpha, type Theme, useTheme } from '@mui/material/styles';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { createFeedback } from '@shared/api/feedback/createFeedback';
import { ActionButton } from '@shared/components/ActionButton';
import { blurActiveElement } from '@shared/lib/dom/blurActiveElement';

const schema = z.object({
  text: z.string().trim().min(1, 'Введите текст обратной связи').max(3000, 'Максимум 3000 символов')
});

type FormValues = z.infer<typeof schema>;

type FeedbackButtonProps = {
  iconOnly?: boolean;
  sidebar?: boolean;
};

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

export const FeedbackButton = ({ iconOnly = false, sidebar = false }: FeedbackButtonProps) => {
  const theme = useTheme();
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting }
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      text: ''
    }
  });

  const currentTextLength = (watch('text') ?? '').length;

  const handleOpen = () => {
    blurActiveElement();
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setError(null);
    setSuccessMessage(null);
    reset({ text: '' });
  };

  const onSubmit = async (values: FormValues) => {
    setError(null);
    setSuccessMessage(null);
    try {
      await createFeedback({ text: values.text.trim() });
      setSuccessMessage('Спасибо! Обратная связь отправлена.');
      reset({ text: '' });
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Не удалось отправить обратную связь');
    }
  };

  return (
    <>
      {sidebar ? (
        <Tooltip title="Обратная связь" placement="right" enterDelay={150} disableHoverListener={!iconOnly}>
          <Box component="span" sx={{ display: 'block', width: '100%' }}>
            <ActionButton
              kind="custom"
              showNavigationIcons={false}
              onClick={handleOpen}
              aria-label="Открыть форму обратной связи"
              sx={{
                width: '100%',
                minHeight: 42,
                minWidth: 0,
                borderRadius: `${theme.acomShape.buttonRadius}px !important`,
                justifyContent: iconOnly ? 'center' : 'flex-start',
                px: iconOnly ? 0 : 1.75,
                gap: iconOnly ? 0 : 1.25,
                transition: 'padding 0.32s ease, gap 0.32s ease'
              }}
            >
              <Box component="span" sx={{ display: 'inline-flex', lineHeight: 1 }}>
                <FeedbackOutlined fontSize="small" />
              </Box>
              <Typography
                sx={{
                  maxWidth: iconOnly ? 0 : 160,
                  opacity: iconOnly ? 0 : 1,
                  transform: iconOnly ? 'translateX(-4px)' : 'translateX(0)',
                  overflow: 'hidden',
                  textOverflow: 'clip',
                  whiteSpace: 'nowrap',
                  fontSize: 14,
                  fontWeight: 500,
                  lineHeight: 1.2,
                  transition: 'max-width 0.34s ease, opacity 0.24s ease, transform 0.34s ease'
                }}
              >
                {'Обратная связь'}
              </Typography>
            </ActionButton>
          </Box>
        </Tooltip>
      ) : iconOnly ? (
        <Tooltip title="Обратная связь" placement="right">
          <Box component="span" sx={{ display: 'block', width: '100%' }}>
            <ActionButton
              kind="custom"
              showNavigationIcons={false}
              onClick={handleOpen}
              aria-label="Открыть форму обратной связи"
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
                <FeedbackOutlined fontSize="small" />
              </Box>
            </ActionButton>
          </Box>
        </Tooltip>
      ) : (
        <Button variant="outlined" onClick={handleOpen}>
          Обратная связь
        </Button>
      )}
      <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm" PaperProps={{ sx: dialogPaperSx }}>
        <DialogContent sx={dialogContentSx}>
          <Box component="form" onSubmit={handleSubmit(onSubmit)}>
            <Stack spacing={2}>
              <Typography variant="h5" fontWeight={600} lineHeight={1}>
                Обратная связь по сервису
              </Typography>

              {error ? <Alert severity="error">{error}</Alert> : null}
              {successMessage ? <Alert severity="success">{successMessage}</Alert> : null}

              <TextField
                label="Ваш отзыв"
                multiline
                minRows={4}
                inputProps={{ maxLength: 3000 }}
                error={Boolean(errors.text)}
                helperText={errors.text ? `${errors.text.message} · ${currentTextLength}/3000` : `${currentTextLength}/3000`}
                {...register('text')}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 1,
                    backgroundColor: 'background.paper',
                    alignItems: 'flex-start'
                  }
                }}
              />

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
                  type="submit"
                  variant="contained"
                  fullWidth
                  disabled={isSubmitting}
                  sx={{ borderRadius: 1, textTransform: 'none', py: 1.1, fontSize: 16, fontWeight: 700, boxShadow: 'none' }}
                >
                  Отправить
                </Button>
              </Stack>
            </Stack>
          </Box>
        </DialogContent>
      </Dialog>
    </>
  );
};
