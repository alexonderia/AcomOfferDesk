import { useEffect, useState } from 'react';
import { Box, Button, Paper, Stack, TextField, Typography } from '@mui/material';
import { useLocation } from 'react-router-dom';
import { useAuth } from '@app/providers/AuthProvider';
import { requestPasswordReset } from '@shared/api/auth';
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
      <Box
        role="status"
        sx={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: 3 }}
      >
        <Typography color="text.secondary">Перенаправляем на страницу входа...</Typography>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 3,
      }}
    >
      <Paper
        elevation={0}
        sx={(theme) => ({
          width: { xs: '94%', sm: 460 },
          borderRadius: 3,
          border: `1px solid ${theme.palette.divider}`,
          backgroundColor: theme.palette.background.paper,
          padding: { xs: 4, sm: 5 },
        })}
      >
        <Stack spacing={3} alignItems="center" textAlign="center">
          <Typography variant="h5" fontWeight={700} color="text.primary">
            Восстановление пароля
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Укажите логин или email. Если учётная запись существует, инструкция придёт на подтверждённый email.
          </Typography>
          <Stack spacing={1.5} sx={{ width: '100%' }}>
            <TextField
              label="Логин или email"
              value={resetLogin}
              onChange={(event) => setResetLogin(event.target.value)}
              autoComplete="username"
              fullWidth
            />
            <Button variant="contained" disabled={isResetting} onClick={() => void submitReset()}>
              Отправить инструкцию
            </Button>
            <Button variant="text" onClick={() => beginLogin(nextPath)}>
              Вернуться ко входу
            </Button>
          </Stack>
        </Stack>
      </Paper>
    </Box>
  );
};
