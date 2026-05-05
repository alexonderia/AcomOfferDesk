import { Box, CircularProgress, Paper, Stack, Typography } from '@mui/material';
import { useEffect, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@app/providers/AuthProvider';
import { getDefaultPathByRole } from '@shared/lib/routing/getDefaultPathByRole';

export const AuthCallbackPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { refresh, session, isAuthenticated } = useAuth();
  const nextPath = useMemo(() => {
    const raw = searchParams.get('next');
    return raw && raw.startsWith('/') ? raw : '/';
  }, [searchParams]);
  const callbackError = searchParams.get('error');

  useEffect(() => {
    if (callbackError) {
      const reason = callbackError === 'not_linked' ? 'not_linked' : 'login_failed';
      navigate(`/login?auth_error=${reason}`, { replace: true });
      return;
    }

    let cancelled = false;
    void refresh('bootstrap').then((restored) => {
      if (!restored && !cancelled) {
        navigate('/login?auth_error=login_failed', { replace: true });
      }
    });

    return () => {
      cancelled = true;
    };
  }, [callbackError, navigate, refresh]);

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

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', p: 3 }}>
      <Paper sx={{ p: 4, width: { xs: '100%', sm: 520 } }}>
        <Stack spacing={2} alignItems="center">
          <Typography variant="h5" fontWeight={700}>Завершаем вход</Typography>
          <CircularProgress size={28} />
          <Typography variant="body2" color="text.secondary" textAlign="center">
            Проверяем доступ и открываем рабочий кабинет.
          </Typography>
        </Stack>
      </Paper>
    </Box>
  );
};
