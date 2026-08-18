import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { Alert, Box, Button, CircularProgress, Paper, Stack, Typography } from '@mui/material';

import { useAuth } from '@app/providers/AuthProvider';
import { verifyEmailToken } from '@shared/api/auth/emailVerification';
import { resolveAuthenticatedPath } from '@shared/lib/routing/resolveAuthenticatedPath';

export const CHECK_EMAIL_NEXT = 'check_email';

const nextActionCopy: Record<string, string> = {
  [CHECK_EMAIL_NEXT]:
    'Мы отправили письмо на указанный адрес. Откройте его и перейдите по ссылке, чтобы подтвердить почту. После подтверждения заявка будет отправлена на проверку.',
  waiting_for_review: 'Email подтверждён. Заявка отправлена на проверку. Мы уведомим вас, когда доступ будет открыт.',
  password_setup: 'Email подтверждён. Создайте пароль по ссылке из письма или кнопке ниже.',
  first_login: 'Email подтверждён. Заполните профиль, чтобы завершить первый вход.',
  login: 'Email подтверждён. Теперь можно войти в систему.',
};

const isPendingEmailVerification = (next: string | null) =>
  next === CHECK_EMAIL_NEXT || next === 'waiting_for_review';

export const VerifyEmailPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { isAuthenticated, session, status } = useAuth();
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [verificationSucceeded, setVerificationSucceeded] = useState(false);
  const [nextAction, setNextAction] = useState<string | null>(searchParams.get('next'));
  const [redirectUrl, setRedirectUrl] = useState<string | null>(null);

  const authenticatedTarget = useMemo(() => {
    if (!session) {
      return null;
    }
    if (session.onboardingState === 'first_login') {
      return '/profile/onboarding';
    }
    return session.businessAccess ? resolveAuthenticatedPath('/', session) : '/account';
  }, [session]);

  useEffect(() => {
    const token = searchParams.get('token');
    if (!token) {
      const pendingNext = searchParams.get('next');
      if (isPendingEmailVerification(pendingNext)) {
        setMessage(nextActionCopy[CHECK_EMAIL_NEXT]);
        setNextAction(CHECK_EMAIL_NEXT);
        setVerificationSucceeded(false);
        setLoading(false);
        return;
      }
      setError('Отсутствует токен подтверждения email.');
      setLoading(false);
      return;
    }

    const run = async () => {
      try {
        const result = await verifyEmailToken(token);
        setNextAction(result.next_action ?? null);
        setRedirectUrl(result.redirect_url ?? null);
        setMessage(nextActionCopy[result.next_action ?? ''] ?? result.detail);
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
    if (nextAction === CHECK_EMAIL_NEXT || nextAction === 'waiting_for_review' || nextAction === 'password_setup') {
      return;
    }
    navigate(authenticatedTarget, { replace: true });
  }, [authenticatedTarget, error, isAuthenticated, loading, navigate, nextAction, verificationSucceeded]);

  const pendingVerification = nextAction === CHECK_EMAIL_NEXT;
  const inviteToken = searchParams.get('invite')?.trim() ?? '';
  const showLoginLink =
    !loading
    && !error
    && (verificationSucceeded || pendingVerification)
    && !isAuthenticated
    && nextAction !== 'password_setup';

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', p: 3 }}>
      <Paper sx={{ p: 4, width: { xs: '100%', sm: 560 } }}>
        <Stack spacing={2} alignItems="center">
          <Typography variant="h5" fontWeight={700}>
            {pendingVerification ? 'Подтвердите email' : 'Подтверждение email'}
          </Typography>
          {loading ? <CircularProgress size={28} /> : null}
          {!loading && error ? <Alert severity="error" sx={{ width: '100%' }}>{error}</Alert> : null}
          {!loading && !error && pendingVerification ? (
            <Alert severity="info" sx={{ width: '100%' }}>{message}</Alert>
          ) : null}
          {pendingVerification && inviteToken ? (
            <Button
              component={Link}
              to={`/register?token=${encodeURIComponent(inviteToken)}`}
              variant="outlined"
              fullWidth
            >
              Изменить данные
            </Button>
          ) : null}
          {!loading && !error && !pendingVerification ? (
            <Alert severity="success" sx={{ width: '100%' }}>{message || 'Email подтверждён.'}</Alert>
          ) : null}
          {nextAction === 'password_setup' && redirectUrl ? (
            <Button href={redirectUrl} variant="contained" fullWidth>
              Создать пароль
            </Button>
          ) : null}
          {showLoginLink ? (
            <Typography variant="body2">
              Перейти к <Link to="/login">входу</Link>
            </Typography>
          ) : null}
          {status === 'unavailable' ? (
            <Typography variant="body2">
              Перейти к <Link to="/login">входу</Link>
            </Typography>
          ) : null}
        </Stack>
      </Paper>
    </Box>
  );
};
