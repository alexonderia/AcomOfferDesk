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
  'User is not active': 'РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ РЅРµР°РєС‚РёРІРµРЅ',
  'User not found': 'РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ РЅРµ РЅР°Р№РґРµРЅ',
  'Invalid credentials': 'РќРµРІРµСЂРЅС‹Р№ Р»РѕРіРёРЅ РёР»Рё РїР°СЂРѕР»СЊ',
  'Missing credentials': 'РћС‚СЃСѓС‚СЃС‚РІСѓСЋС‚ СѓС‡РµС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ',
  'Token expired': 'РЎСЂРѕРє РґРµР№СЃС‚РІРёСЏ С‚РѕРєРµРЅР° РёСЃС‚РµРє',
  'Invalid token': 'РќРµРєРѕСЂСЂРµРєС‚РЅС‹Р№ С‚РѕРєРµРЅ',
  'Invalid token payload': 'РќРµРєРѕСЂСЂРµРєС‚РЅС‹Рµ РґР°РЅРЅС‹Рµ С‚РѕРєРµРЅР°',
  'Link expired': 'РЎСЂРѕРє РґРµР№СЃС‚РІРёСЏ СЃСЃС‹Р»РєРё РёСЃС‚РµРє',
  'Access denied': 'Р”РѕСЃС‚СѓРї Р·Р°РїСЂРµС‰РµРЅ',
  'Request not found': 'Р—Р°СЏРІРєР° РЅРµ РЅР°Р№РґРµРЅР°',
  'Offer not found': 'РљРџ РЅРµ РЅР°Р№РґРµРЅРѕ',
  'Chat not found': 'Р§Р°С‚ РЅРµ РЅР°Р№РґРµРЅ',
  'File not found': 'Р¤Р°Р№Р» РЅРµ РЅР°Р№РґРµРЅ',
  'Message text cannot be empty': 'РўРµРєСЃС‚ СЃРѕРѕР±С‰РµРЅРёСЏ РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј',
  'Too many attachments': 'РЎР»РёС€РєРѕРј РјРЅРѕРіРѕ РІР»РѕР¶РµРЅРёР№',
  'Attachments total size exceeded': 'РџСЂРµРІС‹С€РµРЅ РѕР±С‰РёР№ СЂР°Р·РјРµСЂ РІР»РѕР¶РµРЅРёР№',
  'File too large': 'Р¤Р°Р№Р» СЃР»РёС€РєРѕРј Р±РѕР»СЊС€РѕР№',
  'Unsafe file name': 'РќРµРґРѕРїСѓСЃС‚РёРјРѕРµ РёРјСЏ С„Р°Р№Р»Р°',
  'Forbidden file type': 'РўРёРї С„Р°Р№Р»Р° Р·Р°РїСЂРµС‰РµРЅ',
  'Unsupported file extension': 'РќРµРїРѕРґРґРµСЂР¶РёРІР°РµРјРѕРµ СЂР°СЃС€РёСЂРµРЅРёРµ С„Р°Р№Р»Р°',
  'File cannot be empty': 'Р¤Р°Р№Р» РЅРµ РјРѕР¶РµС‚ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј',
  'File content does not match extension': 'РЎРѕРґРµСЂР¶РёРјРѕРµ С„Р°Р№Р»Р° РЅРµ СЃРѕРѕС‚РІРµС‚СЃС‚РІСѓРµС‚ СЂР°СЃС€РёСЂРµРЅРёСЋ',
  'Only lead economist can manage normative files': 'РўРѕР»СЊРєРѕ РІРµРґСѓС‰РёР№ СЌРєРѕРЅРѕРјРёСЃС‚ РјРѕР¶РµС‚ Р·Р°РіСЂСѓР¶Р°С‚СЊ РЅРѕСЂРјР°С‚РёРІРЅС‹Рµ РґРѕРєСѓРјРµРЅС‚С‹',
  'Normative file can be uploaded only once': 'РќРѕСЂРјР°С‚РёРІРЅС‹Р№ РґРѕРєСѓРјРµРЅС‚ РјРѕР¶РЅРѕ Р·Р°РіСЂСѓР·РёС‚СЊ С‚РѕР»СЊРєРѕ РѕРґРёРЅ СЂР°Р·',
  'Partner card file is not configured': 'РќРµ Р·Р°РіСЂСѓР¶РµРЅ РЅРѕСЂРјР°С‚РёРІРЅС‹Р№ РґРѕРєСѓРјРµРЅС‚ РґР»СЏ РєР°СЂС‚С‹ РїР°СЂС‚РЅРµСЂР°',
  'Insufficient permissions to create manual offers': 'РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ РїСЂР°РІ РґР»СЏ СЂСѓС‡РЅРѕРіРѕ СЃРѕР·РґР°РЅРёСЏ РљРџ',
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
  'Operator can update status only for own requests':
    'РР·РјРµРЅРµРЅРёРµ СЃС‚Р°С‚СѓСЃР° РѕРїРµСЂР°С‚РѕСЂРѕРј РґРѕСЃС‚СѓРїРЅРѕ С‚РѕР»СЊРєРѕ РґР»СЏ СЃРѕР±СЃС‚РІРµРЅРЅС‹С… Р·Р°СЏРІРѕРє',
  'Request is outside your management scope':
    'Р”РµР№СЃС‚РІРёРµ РЅРµРґРѕСЃС‚СѓРїРЅРѕ: Р·Р°СЏРІРєР° РІРЅРµ РІР°С€РµРіРѕ РєРѕРЅС‚СѓСЂР° СѓРїСЂР°РІР»РµРЅРёСЏ',
  'Economist can create manual offers only for own requests': 'Р­РєРѕРЅРѕРјРёСЃС‚ РјРѕР¶РµС‚ СЃРѕР·РґР°РІР°С‚СЊ РљРџ РІСЂСѓС‡РЅСѓСЋ С‚РѕР»СЊРєРѕ РґР»СЏ СЃРІРѕРёС… Р·Р°СЏРІРѕРє',
  'Manual offer can be created only for open request': 'Р СѓС‡РЅРѕРµ РљРџ РјРѕР¶РЅРѕ СЃРѕР·РґР°С‚СЊ С‚РѕР»СЊРєРѕ РґР»СЏ РѕС‚РєСЂС‹С‚РѕР№ Р·Р°СЏРІРєРё',
  'Accepted offer amount is required when request is closed with accepted offer': 'РЈ РїСЂРёРЅСЏС‚РѕРіРѕ РљРџ РґРѕР»Р¶РЅР° Р±С‹С‚СЊ СѓРєР°Р·Р°РЅР° СЃСѓРјРјР°',
  'Unsupported contractor mode': 'РќРµРєРѕСЂСЂРµРєС‚РЅС‹Р№ СЂРµР¶РёРј РІС‹Р±РѕСЂР° РєРѕРЅС‚СЂР°РіРµРЅС‚Р°',
  'Existing contractor is required': 'Р’С‹Р±РµСЂРёС‚Рµ РєРѕРЅС‚СЂР°РіРµРЅС‚Р° РёР· СЃРїРёСЃРєР°',
  'Contractor is required': 'РЈРєР°Р¶РёС‚Рµ РєРѕРЅС‚СЂР°РіРµРЅС‚Р°',
  'Selected user is not contractor': 'Р’С‹Р±СЂР°РЅРЅС‹Р№ РїРѕР»СЊР·РѕРІР°С‚РµР»СЊ РЅРµ СЏРІР»СЏРµС‚СЃСЏ РєРѕРЅС‚СЂР°РіРµРЅС‚РѕРј',
  'Selected contractor must be active': 'Р’С‹Р±СЂР°РЅРЅС‹Р№ РєРѕРЅС‚СЂР°РіРµРЅС‚ РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ Р°РєС‚РёРІРµРЅ',
  'Selected contractor is hidden for this request': 'Р’С‹Р±СЂР°РЅРЅС‹Р№ РєРѕРЅС‚СЂР°РіРµРЅС‚ СЃРєСЂС‹С‚ РґР»СЏ СЌС‚РѕР№ Р·Р°СЏРІРєРё',
  'Only admin and superadmin can manage manually created contractors': 'РўРѕР»СЊРєРѕ Р°РґРјРёРЅРёСЃС‚СЂР°С‚РѕСЂ Рё СЃСѓРїРµСЂР°РґРјРёРЅ РјРѕРіСѓС‚ СЂРµРґР°РєС‚РёСЂРѕРІР°С‚СЊ СЂСѓС‡РЅС‹С… РєРѕРЅС‚СЂР°РіРµРЅС‚РѕРІ',
  'Only manually created contractor can be updated by this endpoint': 'Р РµРґР°РєС‚РёСЂРѕРІР°РЅРёРµ РґРѕСЃС‚СѓРїРЅРѕ С‚РѕР»СЊРєРѕ РґР»СЏ РІСЂСѓС‡РЅСѓСЋ СЃРѕР·РґР°РЅРЅС‹С… РєРѕРЅС‚СЂР°РіРµРЅС‚РѕРІ',
  'Subordinate profile is available only for permitted subordinate roles': 'РџСЂРѕС„РёР»СЊ РїРѕРґС‡РёРЅС‘РЅРЅРѕРіРѕ РґРѕСЃС‚СѓРїРµРЅ С‚РѕР»СЊРєРѕ РґР»СЏ СЂР°Р·СЂРµС€С‘РЅРЅС‹С… СЂРѕР»РµР№ РїРѕРґС‡РёРЅС‘РЅРЅС‹С…',
  'Subordinate data can be managed only for permitted subordinate roles': 'Р”Р°РЅРЅС‹Рµ РїРѕРґС‡РёРЅС‘РЅРЅРѕРіРѕ РјРѕР¶РЅРѕ РёР·РјРµРЅСЏС‚СЊ С‚РѕР»СЊРєРѕ РґР»СЏ СЂР°Р·СЂРµС€С‘РЅРЅС‹С… СЂРѕР»РµР№ РїРѕРґС‡РёРЅС‘РЅРЅС‹С…',
  'You can manage subordinate data only for your subordinates': 'Р’С‹ РјРѕР¶РµС‚Рµ СѓРїСЂР°РІР»СЏС‚СЊ РґР°РЅРЅС‹РјРё С‚РѕР»СЊРєРѕ СЃРІРѕРёС… РїРѕРґС‡РёРЅС‘РЅРЅС‹С…',
  Forbidden: 'Р”РѕСЃС‚СѓРї Р·Р°РїСЂРµС‰РµРЅ'
};

const VALIDATION_TRANSLATIONS: Record<string, string> = {
  'Field required': 'РџРѕР»Рµ РѕР±СЏР·Р°С‚РµР»СЊРЅРѕ РґР»СЏ Р·Р°РїРѕР»РЅРµРЅРёСЏ',
  'Input should be a valid string': 'Р—РЅР°С‡РµРЅРёРµ РґРѕР»Р¶РЅРѕ Р±С‹С‚СЊ СЃС‚СЂРѕРєРѕР№',
  'Input should be a valid integer': 'Р—РЅР°С‡РµРЅРёРµ РґРѕР»Р¶РЅРѕ Р±С‹С‚СЊ С†РµР»С‹Рј С‡РёСЃР»РѕРј',
  'Input should be greater than or equal to 1': 'Р—РЅР°С‡РµРЅРёРµ РґРѕР»Р¶РЅРѕ Р±С‹С‚СЊ Р±РѕР»СЊС€Рµ РёР»Рё СЂР°РІРЅРѕ 1',
  'String should have at least 1 character': 'РњРёРЅРёРјСѓРј 1 СЃРёРјРІРѕР»',
  'String should have at least 3 characters': 'РњРёРЅРёРјСѓРј 3 СЃРёРјРІРѕР»Р°',
  'String should have at least 6 characters': 'РњРёРЅРёРјСѓРј 6 СЃРёРјРІРѕР»РѕРІ',
  'String should have at least 8 characters': 'РњРёРЅРёРјСѓРј 8 СЃРёРјРІРѕР»РѕРІ',
  'String should have at most 72 characters': 'РњР°РєСЃРёРјСѓРј 72 СЃРёРјРІРѕР»Р°',
  'String should have at most 128 characters': 'РњР°РєСЃРёРјСѓРј 128 СЃРёРјРІРѕР»РѕРІ',
  'String should have at most 255 characters': 'РњР°РєСЃРёРјСѓРј 255 СЃРёРјРІРѕР»РѕРІ'
};

const translateText = (message: string | null | undefined): string | null => {
  const normalized = (message ?? '').trim();
  if (!normalized) {
    return null;
  }
  const translated = ERROR_TRANSLATIONS[normalized] ?? VALIDATION_TRANSLATIONS[normalized] ?? null;
  return normalizeUserFacingText(translated ?? normalized, GENERIC_ERROR_MESSAGE);
};

const humanizeLoc = (loc: unknown): string => {
  if (!Array.isArray(loc)) {
    return 'РџРѕР»Рµ';
  }

  const parts = loc
    .filter((item) => typeof item === 'string' && item !== 'body' && item !== 'query' && item !== 'path')
    .map((item) => String(item));

  return parts.length ? parts.join('.') : 'РџРѕР»Рµ';
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



