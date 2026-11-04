import { fetchJson } from '../client';

export type ServiceStatus = {
  key: string;
  name: string;
  status: 'up' | 'down' | 'degraded' | 'disabled';
  response_ms: number | null;
  detail: string;
};

export type SystemStatus = {
  checked_at: string;
  overall: 'healthy' | 'degraded';
  uptime_seconds: number;
  cache_ttl_seconds: number;
  probe_timeout_seconds: number;
  settings: {
    environment: string;
    email_enabled: boolean;
    smtp_configured: boolean;
    imap_configured: boolean;
    file_guard_enabled: boolean;
    secure_cookies: boolean;
    cookie_samesite: string;
    signed_file_link_ttl_seconds: number;
    websocket_ticket_ttl_seconds: number;
  };
  services: ServiceStatus[];
};

export const getSystemStatus = async (signal?: AbortSignal): Promise<SystemStatus> => {
  const response = await fetchJson<{ data: SystemStatus }>(
    '/api/v1/system/status', { method: 'GET', cache: 'no-store', signal },
    'Не удалось получить состояние системы',
  );
  return response.data;
};
