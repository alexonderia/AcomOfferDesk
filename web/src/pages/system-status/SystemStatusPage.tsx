import { Alert, Box, Button, Chip, CircularProgress, Paper, Stack, Typography } from '@mui/material';
import RefreshOutlined from '@mui/icons-material/RefreshOutlined';
import { useSystemStatus } from '@features/system-status/useSystemStatus';
import type { ServiceStatus } from '@shared/api/system/getSystemStatus';

const serviceLabels: Record<ServiceStatus['status'], string> = {
  up: 'Доступен', down: 'Недоступен', degraded: 'Требует внимания', disabled: 'Отключён',
};
const serviceColors = { up: 'success', down: 'error', degraded: 'warning', disabled: 'default' } as const;

const operatingModes = [
  {
    emailEnabled: true,
    title: 'Полный — с почтой',
    features: [
      'Разрешены почтовые уведомления, приглашения, подтверждение почты и восстановление пароля письмом.',
      'Доступ новых сотрудников настраивается с использованием почты.',
      'Отправка и получение писем требуют доступных и настроенных почтовых сервисов.',
    ],
  },
  {
    emailEnabled: false,
    title: 'Ограниченный — без почты',
    features: [
      'Почтовые уведомления, приглашения, подтверждение почты и восстановление пароля письмом отключены.',
      'Сотрудники создаются с логином и начальным паролем. Почта необязательна.',
      'Если пользователь забыл пароль, суперадминистратор может задать ему новый пароль без писем.',
    ],
  },
];

const uptimeLabel = (seconds: number) => {
  const minutes = Math.floor(seconds / 60);
  return `${Math.floor(minutes / 1440)} д ${Math.floor(minutes / 60) % 24} ч ${minutes % 60} мин`;
};

export const SystemStatusPage = () => {
  const { data, error, loading, responseMs, reload } = useSystemStatus();
  const config = data?.settings;
  const settings = config ? [
    ['Окружение', config.environment],
    ['Работа с почтой', config.email_enabled ? 'Включена' : 'Отключена'],
    ['Создание сотрудников', config.email_enabled ? 'С настройкой доступа по почте' : 'С логином и начальным паролем'],
    ['SMTP', config.smtp_configured ? 'Настроен' : 'Не настроен'],
    ['Входящая почта (IMAP)', config.imap_configured ? 'Настроена' : 'Не настроена'],
    ['Проверка файлов', config.file_guard_enabled ? 'Включена' : 'Отключена'],
    ['Cookie только по HTTPS', config.secure_cookies ? 'Да' : 'Нет'],
    ['Защита cookie SameSite', config.cookie_samesite],
    ['Срок ссылки на скачивание', `${config.signed_file_link_ttl_seconds} с`],
    ['Срок билета подключения к чату', `${config.websocket_ticket_ttl_seconds} с`],
  ] : [];

  return (
    <Stack spacing={2}>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} justifyContent="space-between" alignItems={{ sm: 'center' }}>
        <Typography component="h1" variant="h4" fontWeight={700}>Состояние системы</Typography>
        <Button variant="outlined" startIcon={loading ? <CircularProgress size={16} /> : <RefreshOutlined />} disabled={loading} onClick={reload}>
          {loading ? 'Проверяем…' : 'Обновить'}
        </Button>
      </Stack>
      {error ? <Alert severity="error">{error}. {data ? 'Показаны последние полученные данные; состояние могло измениться.' : 'Повторите проверку, когда приложение станет доступно.'}</Alert> : null}
      {!data && loading ? <Typography role="status">Проверяем доступность сервисов…</Typography> : null}
      {data && config ? <>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, minmax(0, 1fr))' }, gap: 1.5 }}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Stack spacing={1}>
              <Typography component="h2" variant="subtitle1" fontWeight={700}>Сервисы</Typography>
              <Chip sx={{ alignSelf: 'flex-start' }} label={error ? 'Данные не обновлены' : data.overall === 'healthy' ? 'Проверки пройдены' : 'Есть замечания'} color={error || data.overall !== 'healthy' ? 'warning' : 'success'} />
              <Typography variant="body2" color="text.secondary">Проверено: {new Date(data.checked_at).toLocaleString('ru-RU')}</Typography>
            </Stack>
          </Paper>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography component="h2" variant="subtitle1" fontWeight={700}>Режим работы</Typography>
            <Typography variant="h6" sx={{ mt: 1 }}>{config.email_enabled ? 'С почтой' : 'Без почты (ограниченный)'}</Typography>
            <Typography variant="body2" color="text.secondary">{config.email_enabled ? 'Почтовые операции разрешены настройкой приложения.' : 'Учётные записи и смена паролей работают без писем.'}</Typography>
          </Paper>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography component="h2" variant="subtitle1" fontWeight={700}>Ответ панели</Typography>
            <Typography variant="h6" sx={{ mt: 1 }}>{responseMs === null ? '—' : `${responseMs} мс`}</Typography>
            <Typography variant="body2" color="text.secondary">Время последнего успешного запроса из браузера.</Typography>
            <Typography variant="body2" color="text.secondary">Текущий процесс API: {uptimeLabel(data.uptime_seconds)}</Typography>
          </Paper>
        </Box>
        <Paper component="section" aria-labelledby="operating-modes-title" variant="outlined" sx={{ p: 2 }}>
          <Typography id="operating-modes-title" component="h2" variant="h5" fontWeight={700} sx={{ mb: 1.5 }}>Доступные режимы работы</Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 1.5 }}>
            {operatingModes.map((mode) => {
              const active = mode.emailEnabled === config.email_enabled;
              return <Box component="article" aria-label={mode.title} key={mode.title} sx={{ p: 2, border: '1px solid', borderColor: active ? 'primary.main' : 'divider', borderRadius: 1, bgcolor: active ? 'action.selected' : 'transparent' }}>
                <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" useFlexGap>
                  <Typography component="h3" variant="subtitle1" fontWeight={700}>{mode.title}</Typography>
                  <Chip size="small" label={active ? (error ? 'Последний известный активный' : 'Активен') : 'Не активен'} color={active ? (error ? 'warning' : 'success') : 'default'} />
                </Stack>
                <Box component="ul" sx={{ m: 0, mt: 1, pl: 2.5 }}>
                  {mode.features.map((feature) => <Typography component="li" variant="body2" key={feature} sx={{ mb: 0.75 }}>{feature}</Typography>)}
                </Box>
              </Box>;
            })}
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1.5 }}>В обоих режимах заявки, КП, чаты, файлы и управление пользователями доступны по правам роли. Смена пароля в профиле и сброс паролей суперадминистратором работают в обоих режимах.</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>Режим задаётся в настройках приложения. Сбой почтового сервиса сам по себе не переключает режим.</Typography>
        </Paper>
        <Typography component="h2" variant="h5" fontWeight={700}>Доступность сервисов</Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, minmax(0, 1fr))', xl: 'repeat(3, minmax(0, 1fr))' }, gap: 1.5 }}>
          {data.services.map((service) => <Paper key={service.key} variant="outlined" sx={{ p: 2, minWidth: 0 }}>
            <Stack spacing={1}>
              <Typography component="h3" variant="subtitle1" fontWeight={700}>{service.name}</Typography>
              <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" useFlexGap>
                <Chip size="small" label={serviceLabels[service.status]} color={serviceColors[service.status]} />
                {service.response_ms !== null ? <Typography variant="body2">{service.response_ms} мс</Typography> : null}
              </Stack>
              <Typography variant="body2" color="text.secondary">{service.detail}</Typography>
            </Stack>
          </Paper>)}
        </Box>
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography component="h2" variant="h5" fontWeight={700} sx={{ mb: 1.5 }}>Текущие настройки</Typography>
          <Box component="dl" sx={{ m: 0, display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 1.5 }}>
            {settings.map(([label, value]) => <Box key={label}>
              <Typography component="dt" variant="body2" color="text.secondary">{label}</Typography>
              <Typography component="dd" variant="body1" sx={{ m: 0, overflowWrap: 'anywhere' }}>{value}</Typography>
            </Box>)}
          </Box>
        </Paper>
        <Alert severity="info">
          Автообновление каждые 30 секунд на открытой вкладке. Результат проверок хранится до {data.cache_ttl_seconds} секунд; ожидание каждого сервиса — до {data.probe_timeout_seconds} секунд.
          {' '}SMTP и IMAP показаны по настройкам, доставка писем не проверяется. Работа фоновых обработчиков отдельно не проверяется.
        </Alert>
      </> : null}
    </Stack>
  );
};
