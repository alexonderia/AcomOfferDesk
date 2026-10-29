import { describe, expect, it } from 'vitest';

import { buildDraft, normalizeDraftValue } from './accountStateDraft';

describe('accountStateDraft', () => {
  it('decodes literal unicode escape sequences from stored profile values', () => {
    expect(normalizeDraftValue('\\u0424\\u0418\\u041e')).toBe('ФИО');
    expect(normalizeDraftValue('\\u0418\\u041d\\u041d')).toBe('ИНН');
  });

  it('treats placeholder values as empty strings after normalization', () => {
    expect(normalizeDraftValue(' Не указано ')).toBe('');
    expect(normalizeDraftValue('null')).toBe('');
    expect(normalizeDraftValue('none')).toBe('');
  });

  it('builds a draft with decoded personal and company fields', () => {
    const draft = buildDraft({
      userId: 'contractor-1',
      roleId: 3,
      status: 'review',
      fullName: '\\u0418\\u0432\\u0430\\u043d\\u043e\\u0432 \\u0418\\u0432\\u0430\\u043d',
      phone: '+79991234567',
      mail: 'contractor@example.com',
      departmentName: null,
      company: {
        companyName: 'ООО Ромашка',
        inn: '\\u0037\\u0037\\u0030\\u0037\\u0030\\u0038\\u0033\\u0038\\u0039\\u0033',
        phone: '+79990000000',
        mail: 'company@example.com',
        address: 'Москва',
        note: 'Тест'
      },
      unavailablePeriod: null,
      unavailablePeriods: [],
      permissions: [],
      actions: {
        view_profile: false,
        update_status: false,
        manage_contractor_unit_bindings: false,
        update_role: false,
        update_manager: false,
        manage_manual_contractor: false,
        manage_own_profile: true,
        manage_credentials: false,
        manage_company_contacts: true,
        manage_own_unavailability: false,
        manage_subordinate_unavailability: false,
      },
    });

    expect(draft.fullName).toBe('Иванов Иван');
    expect(draft.inn).toBe('7707083893');
  });
});
