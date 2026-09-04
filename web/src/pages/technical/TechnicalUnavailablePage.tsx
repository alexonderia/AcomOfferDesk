import { Button } from '@mui/material';
import { AuthPageShell } from '@shared/components/AuthPageShell';

type TechnicalUnavailablePageProps = {
  onRetry?: () => void;
};

export const TechnicalUnavailablePage = ({ onRetry = () => window.location.reload() }: TechnicalUnavailablePageProps) => (
  <AuthPageShell
    title="Ведутся технические работы"
    subtitle="Сервис временно недоступен. Пожалуйста, попробуйте обновить страницу позже."
    maxWidth={520}
  >
    <Button variant="contained" fullWidth onClick={onRetry}>
      Обновить страницу
    </Button>
  </AuthPageShell>
);
