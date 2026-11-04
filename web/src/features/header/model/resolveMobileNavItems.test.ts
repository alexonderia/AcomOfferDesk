import { describe, expect, it } from 'vitest';
import { resolveMobileNavItems } from './resolveMobileNavItems';
import type { HeaderMobileNavItem } from './types';

describe('mobile profile navigation', () => {
  it('keeps More and the profile reachable when five sections are configured', () => {
    const items: HeaderMobileNavItem[] = [
      { key: 'dashboard', label: 'Dashboard' }, { key: 'users', label: 'Users' },
      { key: 'hierarchy', label: 'Hierarchy' }, { key: 'requests', label: 'Requests', to: '/requests' },
      { key: 'more', label: 'More', children: [{ key: 'profile', label: 'Profile' }] },
    ];
    const resolved = resolveMobileNavItems(items);
    expect(resolved.map((item) => item.key)).toEqual(['dashboard', 'users', 'hierarchy', 'more']);
    expect(resolved[3].children?.map((item) => item.key)).toEqual(['requests', 'profile']);
    expect(items[4].children?.map((item) => item.key)).toEqual(['profile']);
  });

  it('preserves short menus and filters disabled entries', () => {
    const items = [{ key: 'requests', label: 'Requests' }, { key: 'hidden', label: 'Hidden', disabled: true }, { key: 'more', label: 'More' }];
    expect(resolveMobileNavItems(items).map((item) => item.key)).toEqual(['requests', 'more']);
  });

  it('keeps every overflow section available in More', () => {
    const items = ['a', 'b', 'c', 'd', 'e', 'more'].map((key) => ({ key, label: key }));
    const resolved = resolveMobileNavItems(items);
    expect(resolved).toHaveLength(4);
    expect(resolved[3].children?.map((item) => item.key)).toEqual(['d', 'e']);
  });
});
