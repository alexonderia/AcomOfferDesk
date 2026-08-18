import { CircularProgress, Stack, Typography } from '@mui/material';
import { useEffect, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@app/providers/AuthProvider';
import { AuthPageShell } from '@shared/components/AuthPageShell';
import { resolveAuthenticatedPath } from '@shared/lib/routing/resolveAuthenticatedPath';

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
    navigate(resolveAuthenticatedPath(nextPath, session), { replace: true });
  }, [isAuthenticated, navigate, nextPath, session]);

  return (
    <AuthPageShell title="Завершаем вход">
      <Stack spacing={2} alignItems="center">
        <CircularProgress size={28} />
        <Typography variant="body2" color="text.secondary" textAlign="center">
          Проверяем доступ и открываем рабочий кабинет.
        </Typography>
      </Stack>
    </AuthPageShell>
  );
};
