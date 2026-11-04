import type { SystemStatus } from '@shared/api/system/getSystemStatus';

export const systemStatusFixture: SystemStatus = {
  checked_at: '2026-11-04T09:00:00Z',
  overall: 'healthy', uptime_seconds: 3660, cache_ttl_seconds: 15, probe_timeout_seconds: 3,
  settings: {
    environment: 'development', email_enabled: false, smtp_configured: false, imap_configured: false,
    file_guard_enabled: true, secure_cookies: false, cookie_samesite: 'lax',
    signed_file_link_ttl_seconds: 300, websocket_ticket_ttl_seconds: 30,
  },
  services: [
    { key: 'backend', name: 'Приложение (API)', status: 'up', response_ms: null, detail: 'Обрабатывает запрос' },
    { key: 'database', name: 'База данных', status: 'up', response_ms: 2.4, detail: 'Запрос выполнен' },
  ],
};
