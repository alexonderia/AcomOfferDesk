import { Box, Button, Paper, Stack, Typography } from '@mui/material';
import { Link, useSearchParams } from 'react-router-dom';

type StatusContent = {
  title: string;
  description: string;
};

const CONTENT_BY_REASON: Record<string, StatusContent> = {
  expired: {
    title: 'Срок действия ссылки истёк',
    description:
      'Запросите новую ссылку на регистрацию и откройте её снова.',
  },
  invalid: {
    title: 'Ссылка недействительна',
    description:
      'Похоже, ссылка повреждена или больше не используется. Откройте новую ссылку на регистрацию.',
  },
  already_registered: {
    title: 'Регистрация уже завершена',
    description:
      'Для этого контакта регистрация уже была начата или завершена. Используйте обычный вход в систему.',
  },
};

const DEFAULT_CONTENT: StatusContent = {
  title: 'Не удалось открыть ссылку',
  description:
    'Попробуйте запросить новую ссылку или вернуться ко входу в систему.',
};

export const RegistrationLinkStatusPage = () => {
  const [searchParams] = useSearchParams();
  const reason = searchParams.get('reason')?.trim() ?? '';
  const content = CONTENT_BY_REASON[reason] ?? DEFAULT_CONTENT;

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 3,
      }}
    >
      <Paper
        elevation={0}
        sx={(theme) => ({
          width: { xs: '100%', sm: 560 },
          p: { xs: 4, sm: 5 },
          borderRadius: 4,
          border: `1px solid ${theme.palette.divider}`,
          backgroundColor: theme.palette.background.paper,
        })}
      >
        <Stack spacing={3} alignItems="center" textAlign="center">
          <Typography variant="h5" fontWeight={700} color="text.primary">
            {content.title}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {content.description}
          </Typography>
          <Stack spacing={1.5} width="100%">
            <Button component={Link} to="/login" variant="contained" fullWidth>
              {'Перейти ко входу'}
            </Button>
            <Button component={Link} to="/" variant="outlined" fullWidth>
              {'На главную'}
            </Button>
          </Stack>
        </Stack>
      </Paper>
    </Box>
  );
};
