import { describe, expect, it } from 'vitest';

import {
  isContractorRequestDetailsPath,
  isRequestDetailsPath,
  matchContractorRequestDetailsPath,
  matchRequestDetailsPath,
} from './parseRequestRoutes';

describe('parseRequestRoutes', () => {
  it('matches numeric request details paths', () => {
    expect(matchRequestDetailsPath('/requests/17')).toBe('17');
    expect(isRequestDetailsPath('/requests/17')).toBe(true);
  });

  it('matches letter-based request details paths', () => {
    expect(matchRequestDetailsPath('/requests/теств')).toBe('теств');
    expect(matchRequestDetailsPath('/requests/ABC-123')).toBe('ABC-123');
    expect(isRequestDetailsPath('/requests/теств')).toBe(true);
  });

  it('decodes percent-encoded request ids from pathname', () => {
    expect(matchRequestDetailsPath('/requests/%D1%82%D0%B5%D1%81%D1%82%D0%B2')).toBe('теств');
    expect(matchContractorRequestDetailsPath('/requests/%D1%82%D0%B5%D1%81%D1%82%D0%B2/contractor')).toBe('теств');
  });

  it('does not treat create page as request details', () => {
    expect(matchRequestDetailsPath('/requests/create')).toBeNull();
    expect(isRequestDetailsPath('/requests/create')).toBe(false);
  });

  it('matches contractor request details paths with any request id', () => {
    expect(matchContractorRequestDetailsPath('/requests/теств/contractor')).toBe('теств');
    expect(matchContractorRequestDetailsPath('/requests/17/contractor')).toBe('17');
    expect(isContractorRequestDetailsPath('/requests/теств/contractor')).toBe(true);
  });
});
