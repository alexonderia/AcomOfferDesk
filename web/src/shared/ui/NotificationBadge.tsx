import Box from '@mui/material/Box';
import MailOutlineRoundedIcon from '@mui/icons-material/MailOutlineRounded';

type NotificationBadgeProps = {
  title?: string;
  size?: number;
};

export const NotificationBadge = ({ title, size = 28 }: NotificationBadgeProps) => (
  <Box
    role="img"
    aria-label={title ?? 'Новое сообщение'}
    sx={{
      width: size,
      height: size,
      borderRadius: '50%',
      border: (theme) => `1px solid ${theme.palette.primary.main}`,
      color: 'primary.main',
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: 'background.paper',
    }}
    title={title}
  >
    <MailOutlineRoundedIcon aria-hidden sx={{ fontSize: size * 0.57 }} />
  </Box>
);
