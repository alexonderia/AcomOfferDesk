const API_PREFIX = '/api/';

export const resolveNotificationLink = (linkUrl: string | null): string | null => {
  if (!linkUrl) {
    return null;
  }

  try {
    if (linkUrl.startsWith('/')) {
      return linkUrl.startsWith(API_PREFIX) ? null : linkUrl;
    }

    const parsed = new URL(linkUrl, window.location.origin);
    if (parsed.origin !== window.location.origin) {
      return null;
    }
    if (parsed.pathname.startsWith(API_PREFIX)) {
      return null;
    }

    return `${parsed.pathname}${parsed.search}${parsed.hash}`;
  } catch {
    return null;
  }
};
