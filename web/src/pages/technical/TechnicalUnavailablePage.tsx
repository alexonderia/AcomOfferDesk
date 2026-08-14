import { Box, Button, Paper, Stack, Typography } from '@mui/material';

type TechnicalUnavailablePageProps = {
  onRetry?: () => void;
};

export const TechnicalUnavailablePage = ({ onRetry = () => window.location.reload() }: TechnicalUnavailablePageProps) => (
  <Box
    sx={{
      minHeight: '100vh',
      display: 'grid',
      placeItems: 'center',
      padding: 3,
      backgroundColor: 'background.default',
    }}
  >
    <Paper
      elevation={0}
      sx={(theme) => ({
        width: { xs: '94%', sm: 520 },
        borderRadius: 3,
        border: `1px solid ${theme.palette.divider}`,
        backgroundColor: theme.palette.background.paper,
        padding: { xs: 4, sm: 5 },
        textAlign: 'center',
      })}
    >
      <Stack spacing={2.5} alignItems="center">
        <Typography variant="h5" fontWeight={700} color="text.primary">
          Ведутся технические работы
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Сервис временно недоступен. Пожалуйста, попробуйте обновить страницу позже.
        </Typography>
        <Button variant="contained" size="large" onClick={onRetry}>
          Обновить страницу
        </Button>
      </Stack>
    </Paper>
  </Box>
);
