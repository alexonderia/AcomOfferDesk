import type { HeaderMobileNavItem } from './types';

export const resolveMobileNavItems = (items: HeaderMobileNavItem[]): HeaderMobileNavItem[] => {
  const enabled = items.filter((item) => !item.disabled);
  if (enabled.length <= 4) return enabled;
  const more = enabled.find((item) => item.key === 'more');
  if (!more) return enabled.slice(0, 4);
  const sections = enabled.filter((item) => item.key !== 'more');
  return [
    ...sections.slice(0, 3),
    { ...more, children: [...sections.slice(3), ...(more.children ?? [])] },
  ];
};
