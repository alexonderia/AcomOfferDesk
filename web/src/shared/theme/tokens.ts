export const themeTokens = {
  color: {
    primary: {
      main: '#3B82F6',
      hover: '#2F6FE3',
      pressed: '#2559C7'
    },
    accent: '#60A5FA',
    background: {
      page: '#F3F5FB',
      card: '#FFFFFF',
      softSection: '#EEF3FB'
    },
    text: {
      primary: '#111827',
      secondary: '#6B7280'
    },
    border: '#DDE3EF',
    status: {
      success: '#22A06B',
      warning: '#F59E0B',
      error: '#EF4444',
      info: '#60A5FA',
      mutedBadge: '#DDEAFE',
      open: '#6fa8dc',
      review: '#f4b183',
      tones: {
        success: { text: '#1f6b43', bg: '#e8f7ee', border: '#b7e2c8' },
        warning: { text: '#8a6d1f', bg: '#fff8e1', border: '#f2dd9b' },
        error: { text: '#9a1f1f', bg: '#ffecec', border: '#f3bcbc' },
        info: { text: '#1565c0', bg: '#e3f2fd', border: '#c1d9f9' },
        neutral: { text: '#4d5563', bg: '#f3f4f8', border: '#d9dde8' }
      }
    },
    chart: ['#3B82F6', '#60A5FA', '#93C5FD', '#2F6FE3', '#BFDBFE'],
    disabled: {
      bg: '#EEF2F7',
      text: '#98A2B3'
    }
  },
  interaction: {
    outlinedHoverBgAlpha: 0.06,
    outlinedPressedBgAlpha: 0.12
  },
  shape: {
    radius: 12,
    radiusLg: 16,
    buttonRadius: 12,
    panelPadding: 16,
    surfacePadding: 8
  },
  typography: {
    fontFamily: '"Inter", "Segoe UI", sans-serif',
    buttonFontSize: 16,
    buttonFontWeight: 600,
    bodyFontSize: 16
  },
  button: {
    minHeight: 44,
    horizontalPadding: 18,
    iconSize: 20,
    borderWidth: 1
  }
} as const;

export type ThemeTokens = typeof themeTokens;
