import '@mui/material/styles';

declare module '@mui/material/styles' {
  interface Theme {
    acomShape: {
      buttonRadius: number;
      controlRadius: number;
      panelPadding: number;
      panelRadius: number;
      surfacePadding: number;
      surfaceRadius: number;
    };
  }

  interface ThemeOptions {
    acomShape?: {
      buttonRadius?: number;
      controlRadius?: number;
      panelPadding?: number;
      panelRadius?: number;
      surfacePadding?: number;
      surfaceRadius?: number;
    };
  }

  type StatusTone = {
    text: string;
    bg: string;
    border: string;
  };

  type StatusTones = {
    success: StatusTone;
    warning: StatusTone;
    error: StatusTone;
    info: StatusTone;
    neutral: StatusTone;
  };

  interface Palette {
    brand: {
      accent: string;
      softSection: string;
      border: string;
      mutedBadge: string;
      chart: string[];
      disabledBg: string;
      disabledText: string;
      primaryHover: string;
      primaryPressed: string;
    };
    statusTones: StatusTones;
    dashboard: {
      status: {
        open: string;
        review: string;
      };
      workload: string[];
    };
  }

  interface PaletteOptions {
    brand?: {
      accent?: string;
      softSection?: string;
      border?: string;
      mutedBadge?: string;
      chart?: string[];
      disabledBg?: string;
      disabledText?: string;
      primaryHover?: string;
      primaryPressed?: string;
    };
    statusTones?: StatusTones;
    dashboard?: {
      status?: {
        open?: string;
        review?: string;
      };
      workload?: string[];
    };
  }
}
