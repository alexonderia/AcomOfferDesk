import { type CurrentUserProfile } from '@shared/api/users/getCurrentUserProfile';
import { formatRuPhone } from '@shared/lib/phone';

export type ProfileDraft = {
  fullName: string;
  phone: string;
  mail: string;
  companyName: string;
  inn: string;
  companyPhone: string;
  companyMail: string;
  address: string;
  note: string;
};

export const emptyDraft: ProfileDraft = {
  fullName: '',
  phone: '',
  mail: '',
  companyName: '',
  inn: '',
  companyPhone: '',
  companyMail: '',
  address: '',
  note: ''
};

const decodeLiteralUnicodeEscapes = (value: string) => (
  value.replace(/\\u([0-9a-fA-F]{4})/g, (_match, hex: string) => String.fromCharCode(parseInt(hex, 16)))
);

export const normalizeDraftValue = (value: string | null | undefined) => {
  const normalized = decodeLiteralUnicodeEscapes((value ?? '').trim());
  if (!normalized) {
    return '';
  }
  if (['не указано', 'none', 'null'].includes(normalized.toLowerCase())) {
    return '';
  }
  return normalized;
};

export const buildDraft = (profile: CurrentUserProfile | null): ProfileDraft => ({
  fullName: normalizeDraftValue(profile?.fullName),
  phone: formatRuPhone(normalizeDraftValue(profile?.phone)),
  mail: normalizeDraftValue(profile?.mail),
  companyName: normalizeDraftValue(profile?.company.companyName),
  inn: normalizeDraftValue(profile?.company.inn),
  companyPhone: formatRuPhone(normalizeDraftValue(profile?.company.phone)),
  companyMail: normalizeDraftValue(profile?.company.mail),
  address: normalizeDraftValue(profile?.company.address),
  note: normalizeDraftValue(profile?.company.note)
});
