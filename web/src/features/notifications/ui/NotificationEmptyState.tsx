import NotificationsNoneRounded from '@mui/icons-material/NotificationsNoneRounded';
import { Stack, Typography } from '@mui/material';

export const NotificationEmptyState = () => (
  <Stack
    spacing={1.25}
    alignItems="center"
    justifyContent="center"
    sx={{ minHeight: 180, px: 2, textAlign: 'center' }}
  >
    <NotificationsNoneRounded color="disabled" />
    <Typography variant="body2" color="text.secondary">
      Пока нет уведомлений
    </Typography>
  </Stack>
);

