import { useEffect, useState } from 'react';
import { Box, Button, Stack, TextField, Typography } from '@mui/material';
import { useLocation } from 'react-router-dom';
import { useAuth } from '@app/providers/AuthProvider';
import { requestPasswordReset } from '@shared/api/auth';
import { AuthPageShell } from '@shared/components/AuthPageShell';
import { useSystemToasts } from '@shared/ui/toasts';
import { TechnicalUnavailablePage } from '@pages/technical';

export const AuthPage = () => {
  const { beginLogin, status } = useAuth();
  const { showErrorToast, showSuccessToast } = useSystemToasts();
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const nextPath = searchParams.get('next') ?? '/';
  const isResetFlow = searchParams.get('reset') === '1';
  const [resetLogin, setResetLogin] = useState('');
  const [isResetting, setIsResetting] = useState(false);
  const [isResetUnavailable, setIsResetUnavailable] = useState(false);

  useEffect(() => {
    if (!isResetFlow) {
      beginLogin(nextPath);
    }
  }, [beginLogin, isResetFlow, nextPath]);

  const submitReset = async () => {
    if (resetLogin.trim().length < 3) {
      showErrorToast('Укажите логин или email');
      return;
    }
    setIsResetting(true);
    try {
      showSuccessToast(await requestPasswordReset(resetLogin));
      setResetLogin('');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Не удалось запросить сброс пароля';
      if (message.toLowerCase().includes('недоступ')) {
        setIsResetUnavailable(true);
      } else {
        showErrorToast(message);
      }
    } finally {
      setIsResetting(false);
    }
  };

  if (status === 'unavailable' || isResetUnavailable) {
    return <TechnicalUnavailablePage />;
  }

  if (!isResetFlow) {
    return (
      <AuthPageShell>
        <Box role="status" sx={{ display: 'grid', placeItems: 'center', py: 2 }}>
          <Typography color="text.secondary">Перенаправляем на страницу входа...</Typography>
        </Box>
      </AuthPageShell>
    );
  }

  return (
    <AuthPageShell
      title="Восстановление доступа"
      subtitle="Введите логин или email. Мы отправим письмо для восстановления, если аккаунт найден."
    >
      <Stack spacing={2.25} sx={{ width: '100%' }}>
        <Stack spacing={1}>
          <Typography
            component="label"
            htmlFor="reset-login"
            variant="inherit"
            sx={{ fontSize: '14px', fontWeight: 600, lineHeight: 1.25, color: '#1f2a44' }}
          >
            Логин или email
          </Typography>
          <TextField
            id="reset-login"
            hiddenLabel
            value={resetLogin}
            onChange={(event) => setResetLogin(event.target.value)}
            autoComplete="username"
            fullWidth
          />
        </Stack>
        <Button variant="contained" fullWidth disabled={isResetting} onClick={() => void submitReset()}>
          Отправить инструкцию
        </Button>
        <Button variant="text" onClick={() => beginLogin(nextPath)}>
          Вернуться ко входу
        </Button>
      </Stack>
    </AuthPageShell>
  );
};
