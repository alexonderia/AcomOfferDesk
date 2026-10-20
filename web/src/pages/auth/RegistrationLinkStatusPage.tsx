import { Button, Stack } from '@mui/material';
import { Link, useSearchParams } from 'react-router-dom';
import { AuthPageShell } from '@shared/components/AuthPageShell';

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
    <AuthPageShell title={content.title} subtitle={content.description} maxWidth={560}>
      <Stack spacing={1.5} width="100%">
        <Button component={Link} to="/login" variant="contained" fullWidth>
          {'Перейти ко входу'}
        </Button>
        <Button component={Link} to="/" variant="outlined" fullWidth>
          {'На главную'}
        </Button>
      </Stack>
    </AuthPageShell>
  );
};
