import { describe, expect, it } from 'vitest';

import { resolveEffectiveDeadline } from './requestDetailsUtils';

describe('resolveEffectiveDeadline', () => {
  it('keeps the user-edited deadline when the request is already in review', () => {
    expect(
      resolveEffectiveDeadline({
        status: 'review',
        statusChanged: false,
        deadline: '2026-11-15',
        todayDate: '2026-10-22',
      }),
    ).toBe('2026-11-15');
  });

  it('uses today when the request is being moved to review', () => {
    expect(
      resolveEffectiveDeadline({
        status: 'review',
        statusChanged: true,
        deadline: '2026-11-15',
        todayDate: '2026-10-22',
      }),
    ).toBe('2026-10-22');
  });

  it('keeps the user-edited deadline in other statuses', () => {
    expect(
      resolveEffectiveDeadline({
        status: 'open',
        statusChanged: false,
        deadline: '2026-11-15',
        todayDate: '2026-10-22',
      }),
    ).toBe('2026-11-15');
  });
});
