export const GENERIC_ERROR_MESSAGE = 'Произошла ошибка. Попробуйте повторить действие.';
export const NETWORK_ERROR_MESSAGE =
  'Нет соединения с сервером. Проверьте подключение к интернету.';
export const FORBIDDEN_ERROR_MESSAGE = 'Недостаточно прав для выполнения действия.';
export const SESSION_EXPIRED_MESSAGE = 'Сессия истекла. Войдите в систему заново.';
export const NOT_FOUND_ERROR_MESSAGE = 'Данные не найдены или были удалены.';
export const SAVE_ERROR_MESSAGE = 'Не удалось сохранить изменения.';
export const LOAD_ERROR_MESSAGE = 'Не удалось загрузить данные.';
export const DELETE_ERROR_MESSAGE = 'Не удалось удалить данные.';

const DIRECT_TRANSLATIONS: Record<string, string> = {
  Unauthorized: SESSION_EXPIRED_MESSAGE,
  Forbidden: FORBIDDEN_ERROR_MESSAGE,
  'Not found': NOT_FOUND_ERROR_MESSAGE,
  'Network Error': NETWORK_ERROR_MESSAGE,
  'Failed to fetch': NETWORK_ERROR_MESSAGE,
  'Internal Server Error': GENERIC_ERROR_MESSAGE,
  'Validation error': GENERIC_ERROR_MESSAGE,
  ValidationError: GENERIC_ERROR_MESSAGE,
  'Unknown error': GENERIC_ERROR_MESSAGE,
  'Something went wrong': GENERIC_ERROR_MESSAGE,
  'Access denied': FORBIDDEN_ERROR_MESSAGE,
  'Save failed': SAVE_ERROR_MESSAGE,
  'Upload failed': SAVE_ERROR_MESSAGE,
  'Delete failed': DELETE_ERROR_MESSAGE,
  'Connection lost': 'Соединение с сервером потеряно.',
  Reconnecting: 'Восстанавливаем соединение с сервером…',
  'Auth failed': SESSION_EXPIRED_MESSAGE,
};

const CONTAINS_TRANSLATIONS: Array<[string, string]> = [
  ['failed to fetch', NETWORK_ERROR_MESSAGE],
  ['network error', NETWORK_ERROR_MESSAGE],
  ['connection refused', NETWORK_ERROR_MESSAGE],
  ['connection reset', NETWORK_ERROR_MESSAGE],
  ['timeout', NETWORK_ERROR_MESSAGE],
  ['forbidden', FORBIDDEN_ERROR_MESSAGE],
  ['unauthorized', SESSION_EXPIRED_MESSAGE],
  ['session expired', SESSION_EXPIRED_MESSAGE],
  ['not found', NOT_FOUND_ERROR_MESSAGE],
  ['internal server error', GENERIC_ERROR_MESSAGE],
  ['validationerror', GENERIC_ERROR_MESSAGE],
  ['validation error', GENERIC_ERROR_MESSAGE],
];

const TECHNICAL_CONTENT_PATTERN =
  /traceback|stack\s*trace|sql|rabbitmq|smtp|typeorm|sequelize|psycopg|jwt|token\s+signature|exception|error\s*:\s*\{|\{\s*"detail"|\[\s*\{\s*"loc"/i;

const containsCyrillic = (value: string) => /[А-Яа-яЁё]/.test(value);
const containsLatin = (value: string) => /[A-Za-z]/.test(value);
const isLikelyMojibake = (value: string) => /(?:Р.|С.){2,}/.test(value);

export const fallbackByHttpStatus = (status: number): string | null => {
  switch (status) {
    case 400:
      return GENERIC_ERROR_MESSAGE;
    case 401:
      return SESSION_EXPIRED_MESSAGE;
    case 403:
      return FORBIDDEN_ERROR_MESSAGE;
    case 404:
      return NOT_FOUND_ERROR_MESSAGE;
    case 409:
      return SAVE_ERROR_MESSAGE;
    case 413:
      return 'Файл слишком большой. Уменьшите размер и повторите попытку.';
    case 422:
      return GENERIC_ERROR_MESSAGE;
    case 429:
      return 'Слишком много запросов. Попробуйте немного позже.';
    case 500:
    case 502:
    case 503:
    case 504:
      return GENERIC_ERROR_MESSAGE;
    default:
      return null;
  }
};

export const fallbackByActionHint = (hint: string | null | undefined): string => {
  const normalized = (hint ?? '').toLowerCase();
  if (!normalized) {
    return GENERIC_ERROR_MESSAGE;
  }
  if (normalized.includes('save') || normalized.includes('сохран')) {
    return SAVE_ERROR_MESSAGE;
  }
  if (normalized.includes('load') || normalized.includes('загруз')) {
    return LOAD_ERROR_MESSAGE;
  }
  if (normalized.includes('delete') || normalized.includes('удал')) {
    return DELETE_ERROR_MESSAGE;
  }
  if (normalized.includes('network') || normalized.includes('соединен')) {
    return NETWORK_ERROR_MESSAGE;
  }
  if (normalized.includes('session') || normalized.includes('сесс')) {
    return SESSION_EXPIRED_MESSAGE;
  }
  if (normalized.includes('forbidden') || normalized.includes('прав')) {
    return FORBIDDEN_ERROR_MESSAGE;
  }
  if (normalized.includes('not found') || normalized.includes('не найден')) {
    return NOT_FOUND_ERROR_MESSAGE;
  }
  return GENERIC_ERROR_MESSAGE;
};

export const normalizeUserFacingText = (
  rawMessage: string | null | undefined,
  fallback: string = GENERIC_ERROR_MESSAGE
): string => {
  const normalized = (rawMessage ?? '').trim();
  if (!normalized) {
    return fallback;
  }

  if (DIRECT_TRANSLATIONS[normalized]) {
    return DIRECT_TRANSLATIONS[normalized];
  }

  const lowered = normalized.toLowerCase();
  for (const [fragment, translation] of CONTAINS_TRANSLATIONS) {
    if (lowered.includes(fragment)) {
      return translation;
    }
  }

  if (TECHNICAL_CONTENT_PATTERN.test(normalized)) {
    return fallback;
  }

  if (isLikelyMojibake(normalized)) {
    return fallback;
  }

  if (containsCyrillic(normalized)) {
    return normalized;
  }

  if (containsLatin(normalized)) {
    return fallback;
  }

  return normalized;
};
