const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export const normalizeAdditionalEmail = (value: string) => value.trim().toLowerCase();

export const splitAdditionalEmails = (value: string): string[] =>
  value
    .split(',')
    .map(normalizeAdditionalEmail)
    .filter(Boolean);

export const isValidAdditionalEmail = (value: string) => EMAIL_PATTERN.test(value);

export const mergeAdditionalEmails = (currentEmails: string[], nextEmails: string[]) =>
  Array.from(new Set([...currentEmails, ...nextEmails]));
