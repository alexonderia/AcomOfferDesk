import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Alert, Box, CircularProgress, Paper, Stack, Typography } from '@mui/material';
import { verifyEmailToken } from '@shared/api/auth/emailVerification';

export const VerifyEmailPage = () => {
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

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
      } catch (verifyError) {
        setError(verifyError instanceof Error ? verifyError.message : 'Не удалось подтвердить email.');
      } finally {
        setLoading(false);
      }
    };

    void run();
  }, [searchParams]);

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', p: 3 }}>
      <Paper sx={{ p: 4, width: { xs: '100%', sm: 560 } }}>
        <Stack spacing={2} alignItems="center">
          <Typography variant="h5" fontWeight={700}>Подтверждение email</Typography>
          {loading ? <CircularProgress size={28} /> : null}
          {!loading && error ? <Alert severity="error" sx={{ width: '100%' }}>{error}</Alert> : null}
          {!loading && !error ? <Alert severity="success" sx={{ width: '100%' }}>{message || 'Email подтвержден.'}</Alert> : null}
          <Typography variant="body2">
            Перейти к <Link to="/login">входу</Link>
          </Typography>
        </Stack>
      </Paper>
    </Box>
  );
};
