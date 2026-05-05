import { Alert, Box, Button, CircularProgress, Paper, Stack, Typography } from '@mui/material';
import { useEffect, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@app/providers/AuthProvider';
import { getDefaultPathByRole } from '@shared/lib/routing/getDefaultPathByRole';

export const AuthPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { beginLogin, isAuthenticated, session, status } = useAuth();
  const isLoggedOut = searchParams.get('logged_out') === '1';
  const nextPath = useMemo(() => {
    const raw = searchParams.get('next')?.trim();
    return raw && raw.startsWith('/') ? raw : '/';
  }, [searchParams]);

  const authErrorMessage = useMemo(() => {
    const reason = (searchParams.get('auth_error') ?? '').trim();
    if (!reason) {
      return null;
    }
    if (reason === 'session_expired') {
      return 'Сессия входа истекла. Нажмите «Войти снова».';
    }
    if (reason === 'access_denied') {
      return 'Вход отменен. Нажмите «Войти снова».';
    }
    if (reason === 'not_linked') {
      return 'Не удалось завершить вход. Обратитесь к администратору, чтобы проверить доступ.';
    }
    if (reason === 'login_failed') {
      return 'Не удалось завершить вход. Нажмите «Войти снова».';
    }
    return 'Не удалось завершить вход. Попробуйте еще раз.';
  }, [searchParams]);

  useEffect(() => {
    if (!isAuthenticated || !session) {
      return;
    }
    if (!session.businessAccess) {
      navigate('/account', { replace: true });
      return;
    }
    navigate(nextPath === '/' ? getDefaultPathByRole(session.roleId) : nextPath, { replace: true });
  }, [isAuthenticated, navigate, nextPath, session]);

  useEffect(() => {
    if (status !== 'anonymous') {
      return;
    }
    if (isLoggedOut) {
      return;
    }
    if (authErrorMessage) {
      return;
    }
    beginLogin(nextPath);
  }, [authErrorMessage, beginLogin, isLoggedOut, nextPath, status]);

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 3
      }}
    >
      <Paper
        elevation={0}
        sx={(theme) => ({
          width: { xs: '94%', sm: 460 },
          borderRadius: 3,
          border: `1px solid ${theme.palette.divider}`,
          backgroundColor: theme.palette.background.paper,
          padding: { xs: 4, sm: 5 }
        })}
      >
        <Stack spacing={3} alignItems="center" textAlign="center">
          <Typography variant="h5" fontWeight={700} color="text.primary">
            Вход в AcomOfferDesk
          </Typography>
          {authErrorMessage ? (
            <>
              <Alert severity="warning" sx={{ width: '100%' }}>
                {authErrorMessage}
              </Alert>
              <Button
                variant="contained"
                onClick={() => beginLogin(nextPath, { forcePrompt: true })}
                sx={{ borderRadius: 999, textTransform: 'none', px: 3 }}
              >
                Войти снова
              </Button>
            </>
          ) : isLoggedOut ? (
            <>
              <Alert severity="info" sx={{ width: '100%' }}>
                Вы вышли из системы.
              </Alert>
              <Button
                variant="contained"
                onClick={() => beginLogin(nextPath)}
                sx={{ borderRadius: 999, textTransform: 'none', px: 3 }}
              >
                Войти
              </Button>
            </>
          ) : (
            <>
              <Typography variant="body2" color="text.secondary">
                Перенаправляем на страницу входа.
              </Typography>
              <CircularProgress size={28} />
            </>
          )}
        </Stack>
      </Paper>
    </Box>
  );
};
