import { themeTokens } from '@shared/theme/tokens';

export const sectionTitleSx = {
  fontSize: themeTokens.typography.captionFontSize,
  fontWeight: 700,
  textTransform: 'uppercase',
  letterSpacing: 0.4,
  color: 'text.secondary',
} as const;
