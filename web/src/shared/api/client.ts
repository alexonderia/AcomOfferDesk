import {
  GENERIC_ERROR_MESSAGE,
  NETWORK_ERROR_MESSAGE,
  fallbackByActionHint,
  fallbackByHttpStatus,
  normalizeUserFacingText,
} from '@shared/lib/errors/userFacing';

type RefreshReason = 'bootstrap' | 'http_401' | 'ws_4401';
type AuthRuntime = {
  refresh: (reason: RefreshReason) => Promise<boolean>;
  canAttemptSilentRefresh: (reason: Exclude<RefreshReason, 'bootstrap'>) => boolean;
  forceLogout: () => void;
};

let authToken: string | null = null;
let authRuntime: AuthRuntime | null = null;

const ERROR_TRANSLATIONS: Record<string, string> = {
  'Не удалось авторизоваться в Keycloak Admin API': 'Не удалось авторизоваться в Keycloak Admin API',
  'Unable to authenticate in Keycloak admin API': 'Не удалось авторизоваться в Keycloak Admin API',
  'Unable to create Keycloak account': 'Не удалось создать учетную запись в Keycloak',
  'Unable to query Keycloak users': 'Не удалось получить пользователей из Keycloak',
  'User is not active': 'Пользователь неактивен',
  'User not found': 'Пользователь не найден',
  'Invalid credentials': 'Неверный логин или пароль',
  'Missing credentials': 'Отсутствуют учетные данные',
  'Token expired': 'Срок действия токена истек',
  'Invalid token': 'Некорректный токен',
  'Invalid token payload': 'Некорректные данные токена',
  'Link expired': 'Срок действия ссылки истек',
  'Access denied': 'Доступ запрещен',
  'Request not found': 'Заявка не найдена',
  'Request id cannot be empty': 'Укажите номер заявки',
  'Request with this id already exists': 'Заявка с таким номером уже существует',
  'Offer not found': 'КП не найдено',
  'Chat not found': 'Чат не найден',
  'File not found': 'Файл не найден',
  'Message text cannot be empty': 'Текст сообщения не может быть пустым',
  'Too many attachments': 'Слишком много вложений',
  'Attachments total size exceeded': 'Превышен общий размер вложений',
  'File too large': 'Файл слишком большой. Размер одного файла не должен превышать 5 МБ.',
  'Unsafe file name': 'Недопустимое имя файла',
  'Forbidden file type': 'Тип файла запрещен',
  'Unsupported file extension': 'Неподдерживаемое расширение файла',
  'File cannot be empty': 'Файл не может быть пустым',
  'File content does not match extension': 'Содержимое файла не соответствует расширению',
  'Only lead economist can manage normative files': 'Только ведущий экономист может загружать нормативные документы',
  'Normative file can be uploaded only once': 'Нормативный документ можно загрузить только один раз',
  'Partner card file is not configured': 'Не загружен нормативный документ для карты партнера',
  'Insufficient permissions to create manual offers': 'Недостаточно прав для ручного создания КП',
  'Insufficient permissions to edit request':
    'РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ РґР»СЏ СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ Р·Р°СЏРІРєРё: РґРѕСЃС‚СѓРї РѕРіСЂР°РЅРёС‡РµРЅ РёРµСЂР°СЂС…РёРµР№/РїРѕРґСЂР°Р·РґРµР»РµРЅРёРµРј',
  'Insufficient permissions to update request status':
    'РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ РґР»СЏ РёР·РјРµРЅРµРЅРёСЏ СЃС‚Р°С‚СѓСЃР° Р·Р°СЏРІРєРё: С‚СЂРµР±СѓРµС‚СЃСЏ РїСЂР°РІРѕ РёР·РјРµРЅРµРЅРёСЏ СЃС‚Р°С‚СѓСЃР° РІ РІР°С€РµРј РєРѕРЅС‚СѓСЂРµ РґРѕСЃС‚СѓРїР°',
  'Offer status cannot be changed for closed request': 'КП нельзя изменить, если заявка уже закрыта или отклонена',
  'КП нельзя изменить, если заявка уже закрыта или отклонена': 'КП нельзя изменить, если заявка уже закрыта или отклонена',
  'Insufficient permissions to update request amounts':
    'РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ РґР»СЏ РёР·РјРµРЅРµРЅРёСЏ СЃСѓРјРј Р·Р°СЏРІРєРё: С‚СЂРµР±СѓРµС‚СЃСЏ РїСЂР°РІРѕ РЅР° СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёРµ С†РµРЅ РІ РІР°С€РµРј РєРѕРЅС‚СѓСЂРµ РґРѕСЃС‚СѓРїР°',
  'Insufficient permissions to update request deadline':
    'РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ РґР»СЏ РёР·РјРµРЅРµРЅРёСЏ РґРµРґР»Р°Р№РЅР° Р·Р°СЏРІРєРё: С‚СЂРµР±СѓРµС‚СЃСЏ РїСЂР°РІРѕ СЂРµРґР°РєС‚РёСЂРѕРІР°РЅРёСЏ РґРµРґР»Р°Р№РЅР° РІ РІР°С€РµРј РєРѕРЅС‚СѓСЂРµ РґРѕСЃС‚СѓРїР°',
  'Insufficient permissions to upload request files':
    'РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ РґР»СЏ Р·Р°РіСЂСѓР·РєРё С„Р°Р№Р»РѕРІ РІ Р·Р°СЏРІРєСѓ: С‚СЂРµР±СѓРµС‚СЃСЏ РїСЂР°РІРѕ Р·Р°РіСЂСѓР·РєРё С„Р°Р№Р»РѕРІ Рё РґРѕСЃС‚СѓРї Рє Р·Р°СЏРІРєРµ',
  'Insufficient permissions to delete request files':
    'РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ РґР»СЏ СѓРґР°Р»РµРЅРёСЏ С„Р°Р№Р»РѕРІ Р·Р°СЏРІРєРё: С‚СЂРµР±СѓРµС‚СЃСЏ РїСЂР°РІРѕ СѓРґР°Р»РµРЅРёСЏ С„Р°Р№Р»РѕРІ Рё РґРѕСЃС‚СѓРї Рє Р·Р°СЏРІРєРµ',
  'Insufficient permissions to send request email notifications':
    'РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ РґР»СЏ РѕС‚РїСЂР°РІРєРё РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅС‹С… СѓРІРµРґРѕРјР»РµРЅРёР№ РїРѕ Р·Р°СЏРІРєРµ',
  'Insufficient permissions to view chat': 'Недостаточно прав для просмотра чата',
  'Insufficient permissions to send chat message': 'Недостаточно прав для отправки сообщения в чат',
  'Insufficient permissions to view workspace': 'Недостаточно прав для просмотра рабочего пространства',
  'Operator can update status only for own requests':
    'РР·РјРµРЅРµРЅРёРµ СЃС‚Р°С‚СѓСЃР° РѕРїРµСЂР°С‚РѕСЂРѕРј РґРѕСЃС‚СѓРїРЅРѕ С‚РѕР»СЊРєРѕ РґР»СЏ СЃРѕР±СЃС‚РІРµРЅРЅС‹С… Р·Р°СЏРІРѕРє',
  'Request is outside your management scope':
    'Р”РµР№СЃС‚РІРёРµ РЅРµРґРѕСЃС‚СѓРїРЅРѕ: Р·Р°СЏРІРєР° РІРЅРµ РІР°С€РµРіРѕ РєРѕРЅС‚СѓСЂР° СѓРїСЂР°РІР»РµРЅРёСЏ',
  'Economist can create manual offers only for own requests': 'Экономист может создавать КП вручную только для своих заявок',
  'Manual offer can be created only for open request': 'Ручное КП можно создать только для открытой заявки',
  'Accepted offer amount is required when request is closed with accepted offer': 'У принятого КП должна быть указана сумма',
  'Unsupported contractor mode': 'Некорректный режим выбора контрагента',
  'Existing contractor is required': 'Выберите контрагента из списка',
  'Contractor is required': 'Укажите контрагента',
  'Selected user is not contractor': 'Выбранный пользователь не является контрагентом',
  'Selected contractor must be active': 'Выбранный контрагент должен быть активен',
  'Selected contractor is hidden for this request': 'Выбранный контрагент скрыт для этой заявки',
  'Only admin and superadmin can manage manually created contractors': 'Только администратор и суперадмин могут редактировать ручных контрагентов',
  'Only manually created contractor can be updated by this endpoint': 'Редактирование доступно только для вручную созданных контрагентов',
  'Subordinate profile is available only for permitted subordinate roles': 'Профиль подчинённого доступен только для разрешённых ролей подчинённых',
  'Subordinate data can be managed only for permitted subordinate roles': 'Данные подчинённого можно изменять только для разрешённых ролей подчинённых',
  'You can manage subordinate data only for your subordinates': 'Вы можете управлять данными только своих подчинённых',
  Forbidden: 'Недостаточно прав для выполнения действия'
};

const VALIDATION_TRANSLATIONS: Record<string, string> = {
  'Field required': 'Поле обязательно для заполнения',
  'Input should be a valid string': 'Значение должно быть строкой',
  'Input should be a valid integer': 'Значение должно быть целым числом',
  'Input should be greater than or equal to 1': 'Значение должно быть больше или равно 1',
  'String should have at least 1 character': 'Минимум 1 символ',
  'String should have at least 3 characters': 'Минимум 3 символа',
  'String should have at least 6 characters': 'Минимум 6 символов',
  'String should have at least 8 characters': 'Минимум 8 символов',
  'String should have at most 72 characters': 'Максимум 72 символа',
  'String should have at most 128 characters': 'Максимум 128 символов',
  'String should have at most 255 characters': 'Максимум 255 символов'
};

const isLikelyMojibake = (value: string): boolean => {
  // Common UTF-8 -> cp1251/latin1 mojibake markers (e.g. "РџРѕР»Рµ")
  return /(?:Р.|С.){2,}/.test(value);
};

const translateText = (message: string | null | undefined): string | null => {
  const normalized = (message ?? '').trim();
  if (!normalized) {
    return null;
  }
  const translated = ERROR_TRANSLATIONS[normalized] ?? VALIDATION_TRANSLATIONS[normalized] ?? null;
  const safeTranslated = translated && !isLikelyMojibake(translated) ? translated : null;
  return normalizeUserFacingText(safeTranslated ?? normalized, GENERIC_ERROR_MESSAGE);
};

const humanizeLoc = (loc: unknown): string => {
  if (!Array.isArray(loc)) {
    return 'Поле';
  }

  const parts = loc
    .filter((item) => typeof item === 'string' && item !== 'body' && item !== 'query' && item !== 'path')
    .map((item) => String(item));

  return parts.length ? parts.join('.') : 'Поле';
};

const extractDetailMessage = (detail: unknown): string | null => {
  if (typeof detail === 'string') {
    return translateText(detail);
  }

  if (Array.isArray(detail)) {
    const validationMessages = detail
      .map((item) => {
        if (!item || typeof item !== 'object') {
          return null;
        }
        const msg = translateText((item as { msg?: string }).msg);
        if (!msg) {
          return null;
        }
        const loc = humanizeLoc((item as { loc?: unknown }).loc);
        return `${loc}: ${msg}`;
      })
      .filter((value): value is string => Boolean(value));

    if (validationMessages.length) {
      return validationMessages.join('; ');
    }
  }

  if (detail && typeof detail === 'object' && 'message' in detail) {
    return translateText((detail as { message?: string }).message);
  }

  return null;
};

export const setAuthToken = (token: string | null) => {
  authToken = token;
};

export const setAuthRuntime = (runtime: AuthRuntime | null) => {
  authRuntime = runtime;
};

const getErrorMessage = async (response: Response, fallback: string) => {
  const data = await response.json().catch(() => null);
  if (data && typeof data === 'object' && 'detail' in data) {
    const detailMessage = extractDetailMessage((data as { detail?: unknown }).detail);
    if (detailMessage) {
      return detailMessage;
    }
  }

  const statusFallback = fallbackByHttpStatus(response.status);
  if (statusFallback) {
    return statusFallback;
  }

  return normalizeUserFacingText(fallback, fallbackByActionHint(fallback));
};

const skipAutoRefresh = (url: string) => (
  url.startsWith('/api/v1/auth/refresh')
  || url.startsWith('/api/v1/auth/logout')
);

const performFetch = async (url: string, init: RequestInit, headers: Headers): Promise<Response> => {
  return await fetch(url, {
    ...init,
    credentials: init.credentials ?? 'include',
    headers
  });
};

export const apiFetch = async (
  url: string,
  init: RequestInit = {},
  withAuth = true,
  allowRetry = true
): Promise<Response> => {
  const headers = new Headers(init.headers);
  if (!headers.has('Accept')) {
    headers.set('Accept', 'application/json');
  }
  if (withAuth && authToken) {
    headers.set('Authorization', `Bearer ${authToken}`);
  }
  if (!(init.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  let response: Response;
  try {
    response = await performFetch(url, init, headers);
  } catch {
    throw new Error(NETWORK_ERROR_MESSAGE);
  }

  if (
    response.status === 401
    && allowRetry
    && withAuth
    && !skipAutoRefresh(url)
    && authRuntime
    && authRuntime.canAttemptSilentRefresh('http_401')
  ) {
    const refreshed = await authRuntime.refresh('http_401');
    if (refreshed) {
      return await apiFetch(url, init, withAuth, false);
    }
    authRuntime.forceLogout();
  }

  return response;
};

export const fetchJson = async <T>(
  url: string,
  init: RequestInit,
  fallbackError: string,
  withAuth = true
): Promise<T> => {
  const response = await apiFetch(url, init, withAuth);

  if (!response.ok) {
    throw new Error(await getErrorMessage(response, fallbackError));
  }

  const contentType = response.headers.get('Content-Type')?.toLowerCase() ?? '';
  const isJsonResponse = contentType.includes('application/json') || contentType.includes('+json');

  if (!isJsonResponse) {
    const raw = await response.text().catch(() => '');
    const trimmed = raw.trim().toLowerCase();
    if (trimmed.startsWith('<!doctype') || trimmed.startsWith('<html')) {
      throw new Error(GENERIC_ERROR_MESSAGE);
    }
    throw new Error(normalizeUserFacingText(fallbackError, fallbackByActionHint(fallbackError)));
  }

  try {
    return await response.json() as T;
  } catch {
    throw new Error(normalizeUserFacingText(fallbackError, fallbackByActionHint(fallbackError)));
  }
};

export const fetchEmpty = async (
  url: string,
  init: RequestInit,
  fallbackError: string,
  withAuth = true
) => {
  const response = await apiFetch(url, init, withAuth);
  if (!response.ok) {
    throw new Error(await getErrorMessage(response, fallbackError));
  }
};



