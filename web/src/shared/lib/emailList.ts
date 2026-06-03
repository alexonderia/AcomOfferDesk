const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const EMAIL_DELIMITER_PATTERN = /[\s,]+/;
const MAX_EMAIL_LENGTH = 254;

export type ParsedEmailList = {
  valid: string[];
  invalid: string[];
};

export const parseEmailList = (rawInput: string): ParsedEmailList => {
  const tokens = rawInput.split(EMAIL_DELIMITER_PATTERN);
  const valid: string[] = [];
  const invalid: string[] = [];
  const validSeen = new Set<string>();
  const invalidSeen = new Set<string>();

  for (const token of tokens) {
    const email = token.trim().toLowerCase();
    if (!email) {
      continue;
    }
    if (email.length > MAX_EMAIL_LENGTH || !EMAIL_PATTERN.test(email)) {
      if (!invalidSeen.has(email)) {
        invalidSeen.add(email);
        invalid.push(email);
      }
      continue;
    }
    if (!validSeen.has(email)) {
      validSeen.add(email);
      valid.push(email);
    }
  }

  return { valid, invalid };
};
