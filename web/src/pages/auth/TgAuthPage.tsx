// LEGACY_TELEGRAM: page is excluded from active routes and kept only for rollback.
import { Box, Button, Paper, Stack, Typography } from '@mui/material';
import { useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '@app/providers/AuthProvider';

export const TgAuthPage = () => {
  const [searchParams] = useSearchParams();
  const { beginLogin } = useAuth();
  const nextPath = useMemo(() => {
    const raw = searchParams.get('next')?.trim();
    return raw && raw.startsWith('/') ? raw : '/';
  }, [searchParams]);

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', p: 3 }}>
      <Paper sx={{ p: 4, width: { xs: '100%', sm: 520 } }}>
        <Stack spacing={2} alignItems="center">
          <Typography variant="h5" fontWeight={700}>
            Вход по этой ссылке отключен
          </Typography>
          <Typography variant="body2" color="text.secondary" textAlign="center">
            Используйте обычный вход в систему.
          </Typography>
          <Button
            variant="contained"
            onClick={() => beginLogin(nextPath)}
            sx={{ borderRadius: 999, textTransform: 'none', px: 3 }}
          >
            Перейти ко входу
          </Button>
        </Stack>
      </Paper>
    </Box>
  );
};
