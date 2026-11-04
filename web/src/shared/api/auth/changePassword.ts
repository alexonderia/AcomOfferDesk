import { fetchEmpty, fetchJson } from '../client';

export const getAppCapabilities = () => fetchJson<{ data: { email_enabled: boolean } }>(
  '/api/v1/auth/capabilities', { method: 'GET' }, 'Не удалось загрузить режим приложения', false,
);

export const changePassword = (payload: { current_password: string; new_password: string; password_confirmation: string }) =>
  fetchEmpty('/api/v1/users/me/password', { method: 'POST', body: JSON.stringify(payload) }, 'Не удалось изменить пароль');
