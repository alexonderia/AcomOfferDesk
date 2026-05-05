import type { UserTab } from './constants';

export const resolveUserTabFromParam = (value: string | null): UserTab => {
  if (
    value === 'economists' ||
    value === 'admins' ||
    value === 'lead_economists' ||
    value === 'project_managers' ||
    value === 'operators'
  ) {
    return value;
  }
  return 'contractors';
};

const normalizeActionHref = (href: string) => {
  const normalizedHref = href.trim();
  if (!normalizedHref) return '';

  const url = normalizedHref.startsWith('http')
    ? new URL(normalizedHref)
    : new URL(normalizedHref, 'http://local');

  return url.pathname.replace(/\/{2,}/g, '/').replace(/\/$/, '');
};

export const canPatchUserStatus = (href: string, method: string) => {
  if (method.trim().toUpperCase() !== 'PATCH') return false;
  return /^\/api\/v1\/users\/(\{user_id\}|[^/]+)\/status$/.test(normalizeActionHref(href));
};

export const canPatchUserRole = (href: string, method: string) => {
  if (method.trim().toUpperCase() !== 'PATCH') return false;
  return /^\/api\/v1\/users\/(\{user_id\}|[^/]+)\/role$/.test(normalizeActionHref(href));
};
