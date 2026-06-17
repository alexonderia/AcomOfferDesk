import type { UserListItem } from '@entities/user';
import type { UpdateManualContractorPayload } from '@shared/api/users/updateManualContractor';
import { formatRuPhone, isValidRuPhone } from '@shared/lib/phone';

export const NOT_SPECIFIED_TEXT = 'Не указано';

const OPTIONAL_PLACEHOLDER_VALUES = new Set(['не указано', 'none', 'null']);

export const normalizeOptionalContractorValue = (value: string | null | undefined): string => {
  const normalized = (value ?? '').trim();
  if (!normalized || OPTIONAL_PLACEHOLDER_VALUES.has(normalized.toLowerCase())) {
    return '';
  }
  return normalized;
};

export const toOptionalContractorPayloadValue = (value: string): string => {
  const normalized = normalizeOptionalContractorValue(value);
  return normalized || NOT_SPECIFIED_TEXT;
};

const isEmptyOptionalValue = (value: string | undefined) => {
  if (value === undefined) {
    return true;
  }
  return !normalizeOptionalContractorValue(value);
};

export type ManualContractorDraft = {
  login: string;
  full_name: string;
  phone: string;
  mail: string;
  company_name: string;
  inn: string;
  company_phone: string;
  company_mail: string;
  address: string;
  note: string;
};

export type ManualContractorEditableField = Exclude<keyof ManualContractorDraft, 'login'>;
export type ManualContractorField = ManualContractorEditableField | 'password';
export type ManualContractorFieldErrors = Partial<Record<ManualContractorField, string>>;

const MANUAL_EDITABLE_FIELDS: ManualContractorEditableField[] = [
  'full_name',
  'phone',
  'mail',
  'company_name',
  'inn',
  'company_phone',
  'company_mail',
  'address',
  'note',
];

const emailRegex = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const utf8ByteLength = (value: string) => new TextEncoder().encode(value).length;

export const buildManualContractorDraft = (user: UserListItem): ManualContractorDraft => ({
  login: user.user_id,
  full_name: normalizeOptionalContractorValue(user.full_name),
  phone: formatRuPhone(normalizeOptionalContractorValue(user.phone)) || '',
  mail: normalizeOptionalContractorValue(user.mail),
  company_name: normalizeOptionalContractorValue(user.company_name),
  inn: normalizeOptionalContractorValue(user.inn),
  company_phone: formatRuPhone(normalizeOptionalContractorValue(user.company_phone)) || '',
  company_mail: normalizeOptionalContractorValue(user.company_mail),
  address: normalizeOptionalContractorValue(user.address),
  note: normalizeOptionalContractorValue(user.note),
});

export const buildManualContractorPayload = (
  user: UserListItem,
  draft: ManualContractorDraft,
  password = ''
) => {
  const originalPhone = formatRuPhone(normalizeOptionalContractorValue(user.phone)) || '';
  const originalCompanyPhone = formatRuPhone(normalizeOptionalContractorValue(user.company_phone)) || '';
  const trimmedDraft: ManualContractorDraft = {
    login: draft.login.trim(),
    full_name: draft.full_name.trim(),
    phone: draft.phone.trim(),
    mail: draft.mail.trim(),
    company_name: draft.company_name.trim(),
    inn: draft.inn.trim(),
    company_phone: draft.company_phone.trim(),
    company_mail: draft.company_mail.trim(),
    address: draft.address.trim(),
    note: draft.note.trim(),
  };
  const trimmedPassword = password.trim();

  const payload: UpdateManualContractorPayload = {
    ...(trimmedPassword ? { password: trimmedPassword } : {}),
    ...(normalizeOptionalContractorValue(trimmedDraft.full_name) !== normalizeOptionalContractorValue(user.full_name)
      ? { full_name: toOptionalContractorPayloadValue(trimmedDraft.full_name) }
      : {}),
    ...(normalizeOptionalContractorValue(trimmedDraft.phone) !== originalPhone
      ? { phone: toOptionalContractorPayloadValue(trimmedDraft.phone) }
      : {}),
    ...(normalizeOptionalContractorValue(trimmedDraft.mail) !== normalizeOptionalContractorValue(user.mail)
      ? { mail: toOptionalContractorPayloadValue(trimmedDraft.mail) }
      : {}),
    ...(normalizeOptionalContractorValue(trimmedDraft.company_name) !== normalizeOptionalContractorValue(user.company_name)
      ? { company_name: toOptionalContractorPayloadValue(trimmedDraft.company_name) }
      : {}),
    ...(normalizeOptionalContractorValue(trimmedDraft.inn) !== normalizeOptionalContractorValue(user.inn)
      ? { inn: toOptionalContractorPayloadValue(trimmedDraft.inn) }
      : {}),
    ...(normalizeOptionalContractorValue(trimmedDraft.company_phone) !== originalCompanyPhone
      ? { company_phone: toOptionalContractorPayloadValue(trimmedDraft.company_phone) }
      : {}),
    ...(normalizeOptionalContractorValue(trimmedDraft.company_mail) !== normalizeOptionalContractorValue(user.company_mail)
      ? { company_mail: toOptionalContractorPayloadValue(trimmedDraft.company_mail) }
      : {}),
    ...(normalizeOptionalContractorValue(trimmedDraft.address) !== normalizeOptionalContractorValue(user.address)
      ? { address: toOptionalContractorPayloadValue(trimmedDraft.address) }
      : {}),
    ...(normalizeOptionalContractorValue(trimmedDraft.note) !== normalizeOptionalContractorValue(user.note)
      ? { note: toOptionalContractorPayloadValue(trimmedDraft.note) }
      : {}),
  };

  return { trimmedDraft, payload };
};

export const validateContractorEditRow = (
  user: UserListItem,
  manualDraft: ManualContractorDraft,
): ManualContractorFieldErrors => {
  const originalDraft = buildManualContractorDraft(user);
  const hasRowEdits = MANUAL_EDITABLE_FIELDS.some(
    (field) => normalizeOptionalContractorValue(manualDraft[field])
      !== normalizeOptionalContractorValue(originalDraft[field]),
  );

  if (!hasRowEdits) {
    return {};
  }

  const payload: UpdateManualContractorPayload = {};

  for (const field of MANUAL_EDITABLE_FIELDS) {
    const value = manualDraft[field].trim();
    const originalValue = originalDraft[field].trim();
    const isDirty = normalizeOptionalContractorValue(value) !== normalizeOptionalContractorValue(originalValue);
    const normalizedValue = normalizeOptionalContractorValue(value);

    if (isDirty) {
      payload[field] = toOptionalContractorPayloadValue(value);
      continue;
    }

    if (normalizedValue) {
      payload[field] = toOptionalContractorPayloadValue(value);
    }
  }

  return validateManualContractorPayload(payload).fieldErrors;
};

export const validateManualContractorPayload = (
  payload: UpdateManualContractorPayload
): { fieldErrors: ManualContractorFieldErrors; firstError: string | null } => {
  const fieldErrors: ManualContractorFieldErrors = {};

  const setFieldError = (field: ManualContractorField, message: string) => {
    if (!fieldErrors[field]) {
      fieldErrors[field] = message;
    }
  };

  for (const [key, value] of Object.entries(payload)) {
    if (typeof value === 'string' && !value.trim()) {
      if (key === 'password') {
        setFieldError(key as ManualContractorField, 'Поле не может быть пустым');
      }
    }
  }

  if (
    payload.password !== undefined
    && (payload.password.length < 6 || payload.password.length > 72 || utf8ByteLength(payload.password) > 72)
  ) {
    setFieldError('password', 'Пароль должен содержать от 6 до 72 символов (не более 72 байт)');
  }

  if (payload.phone !== undefined && !isEmptyOptionalValue(payload.phone) && !isValidRuPhone(payload.phone)) {
    setFieldError('phone', 'Некорректный формат телефона контакта');
  }

  if (
    payload.company_phone !== undefined
    && !isEmptyOptionalValue(payload.company_phone)
    && !isValidRuPhone(payload.company_phone)
  ) {
    setFieldError('company_phone', 'Некорректный формат телефона компании');
  }

  if (payload.mail !== undefined && !isEmptyOptionalValue(payload.mail) && !emailRegex.test(payload.mail)) {
    setFieldError('mail', 'Некорректный формат e-mail контакта');
  }

  if (
    payload.company_mail !== undefined
    && !isEmptyOptionalValue(payload.company_mail)
    && !emailRegex.test(payload.company_mail)
  ) {
    setFieldError('company_mail', 'Некорректный формат e-mail компании');
  }

  if (payload.inn !== undefined && !isEmptyOptionalValue(payload.inn) && !/^\d{10}$|^\d{12}$/.test(payload.inn)) {
    setFieldError('inn', 'ИНН должен содержать 10 или 12 цифр');
  }

  if (payload.full_name !== undefined && !isEmptyOptionalValue(payload.full_name) && payload.full_name.length > 256) {
    setFieldError('full_name', 'Максимальная длина ФИО — 256 символов');
  }
  if (payload.phone !== undefined && !isEmptyOptionalValue(payload.phone) && payload.phone.length > 64) {
    setFieldError('phone', 'Максимальная длина телефона — 64 символа');
  }
  if (payload.mail !== undefined && !isEmptyOptionalValue(payload.mail) && payload.mail.length > 256) {
    setFieldError('mail', 'Максимальная длина e-mail — 256 символов');
  }
  if (
    payload.company_name !== undefined
    && !isEmptyOptionalValue(payload.company_name)
    && payload.company_name.length > 256
  ) {
    setFieldError('company_name', 'Максимальная длина наименования — 256 символов');
  }
  if (payload.inn !== undefined && !isEmptyOptionalValue(payload.inn) && payload.inn.length > 32) {
    setFieldError('inn', 'Максимальная длина ИНН — 32 символа');
  }
  if (
    payload.company_phone !== undefined
    && !isEmptyOptionalValue(payload.company_phone)
    && payload.company_phone.length > 64
  ) {
    setFieldError('company_phone', 'Максимальная длина телефона — 64 символа');
  }
  if (
    payload.company_mail !== undefined
    && !isEmptyOptionalValue(payload.company_mail)
    && payload.company_mail.length > 256
  ) {
    setFieldError('company_mail', 'Максимальная длина e-mail — 256 символов');
  }
  if (payload.address !== undefined && !isEmptyOptionalValue(payload.address) && payload.address.length > 256) {
    setFieldError('address', 'Максимальная длина адреса — 256 символов');
  }
  if (payload.note !== undefined && !isEmptyOptionalValue(payload.note) && payload.note.length > 1024) {
    setFieldError('note', 'Максимальная длина примечания — 1024 символа');
  }

  return {
    fieldErrors,
    firstError: Object.values(fieldErrors)[0] ?? null,
  };
};
