import { describe, expect, it } from 'vitest';
import type { UserListItem } from '@entities/user';
import {
  buildManualContractorDraft,
  buildManualContractorPayload,
  NOT_SPECIFIED_TEXT,
  normalizeOptionalContractorValue,
  validateContractorEditRow,
  validateManualContractorPayload,
} from './manualContractorEditing';

const buildUser = (overrides: Partial<UserListItem> = {}): UserListItem => ({
  user_id: 'contractor-1',
  role_id: 3,
  id_parent: null,
  status: 'active',
  full_name: 'Иван Петров',
  phone: '+79990000000',
  mail: 'ivan@example.com',
  company_name: 'ООО Ромашка',
  inn: '1234567890',
  company_phone: '+79990000001',
  company_mail: 'office@example.com',
  address: 'Москва',
  note: 'Тест',
  units_count: 0,
  managers_count: 0,
  subordinates_count: 0,
  actions: {
    view_profile: true,
    update_status: true,
    manage_contractor_unit_bindings: false,
    update_role: false,
    update_manager: false,
    manage_own_profile: false,
    manage_credentials: false,
    manage_company_contacts: false,
    manage_own_unavailability: false,
    manage_subordinate_unavailability: false,
    manage_manual_contractor: true,
  },
  ...overrides,
});

describe('manualContractorEditing optional placeholders', () => {
  it('normalizes "Не указано" to empty value', () => {
    expect(normalizeOptionalContractorValue(' Не указано ')).toBe('');
    expect(normalizeOptionalContractorValue('none')).toBe('');
  });

  it('builds draft without placeholder values', () => {
    const draft = buildManualContractorDraft(buildUser({
      mail: NOT_SPECIFIED_TEXT,
      inn: NOT_SPECIFIED_TEXT,
      note: NOT_SPECIFIED_TEXT,
    }));

    expect(draft.mail).toBe('');
    expect(draft.inn).toBe('');
    expect(draft.note).toBe('');
  });

  it('does not validate placeholder optional fields as format errors', () => {
    const { fieldErrors } = validateManualContractorPayload({
      company_name: 'ООО Ландыш',
      mail: NOT_SPECIFIED_TEXT,
      phone: NOT_SPECIFIED_TEXT,
      inn: NOT_SPECIFIED_TEXT,
      company_mail: NOT_SPECIFIED_TEXT,
      company_phone: NOT_SPECIFIED_TEXT,
    });

    expect(fieldErrors).toEqual({});
  });

  it('sends placeholder values when optional field is cleared', () => {
    const user = buildUser();
    const draft = buildManualContractorDraft(user);
    const { payload } = buildManualContractorPayload(user, {
      ...draft,
      note: '',
    });

    expect(payload.note).toBe(NOT_SPECIFIED_TEXT);
  });

  it('treats "Не указано" edits as unchanged for row validation', () => {
    const user = buildUser({ inn: NOT_SPECIFIED_TEXT, note: NOT_SPECIFIED_TEXT });
    const draft = buildManualContractorDraft(user);

    expect(validateContractorEditRow(user, {
      ...draft,
      company_name: 'ООО Ландыш',
    })).toEqual({});

    expect(validateContractorEditRow(user, {
      ...draft,
      inn: NOT_SPECIFIED_TEXT,
      company_name: 'ООО Ландыш',
    })).toEqual({});
  });

  it('still validates invalid unchanged optional values during row edit', () => {
    const user = buildUser({ inn: 'yyyyyyyyy' });
    const draft = buildManualContractorDraft(user);

    expect(validateContractorEditRow(user, {
      ...draft,
      company_name: 'ООО Ландыш',
    })).toEqual({
      inn: 'ИНН должен содержать 10 или 12 цифр',
    });
  });
});
