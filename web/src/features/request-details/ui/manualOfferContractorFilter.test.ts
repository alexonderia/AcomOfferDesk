import { describe, expect, it } from 'vitest';
import type { RequestContractorItem } from '@shared/api/users/getRequestContractors';
import {
  contractorSearchText,
  filterManualOfferContractors
} from './manualOfferContractorFilter';

const contractors: RequestContractorItem[] = [
  {
    user_id: 'test_contr_23',
    full_name: 'Иван Петров',
    company_name: 'ООО Ромашка',
    mail: 'ivan@example.com',
    company_mail: 'office@example.com'
  },
  {
    user_id: 'manual_contractor',
    full_name: 'Не указано',
    company_name: 'ООО Лютик',
    mail: 'Не указано',
    company_mail: 'az0msocc@nhml.com'
  }
];

const filter = (inputValue: string) =>
  filterManualOfferContractors(contractors, {
    inputValue,
    getOptionLabel: contractorSearchText
  });

describe('filterManualOfferContractors', () => {
  it('находит контрагента по email компании', () => {
    expect(filter('az0msocc@nhml.com').map((item) => item.user_id)).toEqual([
      'manual_contractor'
    ]);
  });

  it('находит контрагента по личному email', () => {
    expect(filter('ivan@example.com').map((item) => item.user_id)).toEqual([
      'test_contr_23'
    ]);
  });

  it('находит контрагента по логину', () => {
    expect(filter('test_contr_23').map((item) => item.user_id)).toEqual([
      'test_contr_23'
    ]);
  });

  it('сохраняет поиск по компании и ФИО', () => {
    expect(filter('ромашка').map((item) => item.user_id)).toEqual(['test_contr_23']);
    expect(filter('петров').map((item) => item.user_id)).toEqual(['test_contr_23']);
  });

  it('не находит посторонний email', () => {
    expect(filter('nobody@example.com')).toEqual([]);
  });
});
