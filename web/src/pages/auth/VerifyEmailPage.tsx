import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { Alert, Box, CircularProgress, Paper, Stack, Typography } from '@mui/material';

import { useAuth } from '@app/providers/AuthProvider';
import { verifyEmailToken } from '@shared/api/auth/emailVerification';
import { resolveAuthenticatedPath } from '@shared/lib/routing/resolveAuthenticatedPath';

export const VerifyEmailPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { isAuthenticated, session, status } = useAuth();
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [verificationSucceeded, setVerificationSucceeded] = useState(false);

  const authenticatedTarget = useMemo(() => {
    if (!session) {
      return null;
    }
    return session.businessAccess ? resolveAuthenticatedPath('/', session) : '/account';
  }, [session]);

  useEffect(() => {
    const token = searchParams.get('token');
    if (!token) {
      setError('Отсутствует токен подтверждения email.');
      setLoading(false);
      return;
    }

    const run = async () => {
      try {
        const result = await verifyEmailToken(token);
        setMessage(result.detail);
        setVerificationSucceeded(true);
      } catch (verifyError) {
        setError(verifyError instanceof Error ? verifyError.message : 'Не удалось подтвердить email.');
      } finally {
        setLoading(false);
      }
    };

    void run();
  }, [searchParams]);

  useEffect(() => {
    if (loading || error || !verificationSucceeded || !isAuthenticated || !authenticatedTarget) {
      return;
    }
    navigate(authenticatedTarget, { replace: true });
  }, [authenticatedTarget, error, isAuthenticated, loading, navigate, verificationSucceeded]);

  const waitingForSessionRestore = !loading && !error && verificationSucceeded && status === 'bootstrapping';
  const showLoginLink = !loading && !error && verificationSucceeded && status !== 'bootstrapping' && !isAuthenticated;

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', p: 3 }}>
      <Paper sx={{ p: 4, width: { xs: '100%', sm: 560 } }}>
        <Stack spacing={2} alignItems="center">
          <Typography variant="h5" fontWeight={700}>Подтверждение email</Typography>
          {loading ? <CircularProgress size={28} /> : null}
          {!loading && error ? <Alert severity="error" sx={{ width: '100%' }}>{error}</Alert> : null}
          {!loading && !error ? <Alert severity="success" sx={{ width: '100%' }}>{message || 'Email подтверждён.'}</Alert> : null}
          {waitingForSessionRestore ? (
            <Typography variant="body2" color="text.secondary">
              Восстанавливаем сессию и открываем профиль.
            </Typography>
          ) : null}
          {showLoginLink ? (
            <Typography variant="body2">
              Перейти к <Link to="/login">входу</Link>
            </Typography>
          ) : null}
        </Stack>
      </Paper>
    </Box>
  );
};
