import { Alert, Box, Paper, Stack, Typography } from '@mui/material';

export const AuthPage = () => (
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
        <Alert severity="warning" sx={{ width: '100%' }}>
          Сервис авторизации временно недоступен
        </Alert>
        <Typography variant="body2" color="text.secondary">
          Доступ к защищённым разделам будет восстановлен после подключения нового сервиса авторизации.
        </Typography>
      </Stack>
    </Paper>
  </Box>
);
