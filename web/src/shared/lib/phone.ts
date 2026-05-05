const extractDigits = (value: string) => value.replace(/\D/g, '');

const normalizeRuPhoneDigits = (value: string) => {
  const digits = extractDigits(value);
  if (!digits) {
    return '';
  }

  if (digits[0] === '8') {
    return `7${digits.slice(1, 11)}`;
  }
  if (digits[0] === '7') {
    return digits.slice(0, 11);
  }
  return `7${digits.slice(0, 10)}`;
};

export const isValidRuPhone = (value: string) => {
  const digits = extractDigits(value);
  return digits.length === 11 && (digits[0] === '7' || digits[0] === '8');
};

export const formatRuPhone = (value: string | null | undefined) => {
  const normalized = normalizeRuPhoneDigits(value ?? '');
  if (!normalized) {
    return '';
  }

  const national = normalized.slice(1);
  const part1 = national.slice(0, 3);
  const part2 = national.slice(3, 6);
  const part3 = national.slice(6, 8);
  const part4 = national.slice(8, 10);

  let formatted = '+7';
  if (part1) {
    formatted += ` (${part1}`;
    if (part1.length === 3) {
      formatted += ')';
    }
  }
  if (part2) {
    formatted += ` ${part2}`;
  }
  if (part3) {
    formatted += `-${part3}`;
  }
  if (part4) {
    formatted += `-${part4}`;
  }

  return formatted;
};
