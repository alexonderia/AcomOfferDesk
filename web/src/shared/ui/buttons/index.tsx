import type { ButtonProps } from '@mui/material/Button';
import Button from '@mui/material/Button';
import { alpha, useTheme } from '@mui/material/styles';
import type { SxProps, Theme } from '@mui/material/styles';

type ActionButtonKind = 'custom' | 'filled' | 'outlined';

export type ActionButtonProps = Omit<ButtonProps, 'variant' | 'color'> & {
  kind?: ActionButtonKind;
  selected?: boolean;
  showNavigationIcons?: boolean;
};

export const ActionButton = ({
  kind = 'custom',
  selected = false,
  sx,
  ...props
}: ActionButtonProps) => {
  const theme = useTheme();
  const variant: ButtonProps['variant'] = kind === 'filled' ? 'contained' : kind === 'outlined' ? 'outlined' : 'text';

  const selectedSx: SxProps<Theme> | null = selected
    ? kind === 'custom'
      ? {
          backgroundColor: theme.palette.primary.main,
          borderColor: theme.palette.primary.main,
          color: theme.palette.primary.contrastText,
          '&:hover': {
            backgroundColor: theme.palette.brand.primaryHover,
            borderColor: theme.palette.brand.primaryHover,
          },
        }
      : {
          color: 'primary.main',
          backgroundColor: alpha(theme.palette.primary.main, 0.08),
        }
    : null;

  const baseSx: SxProps<Theme> = {
    textTransform: 'none',
    fontWeight: 600,
    minWidth: 0,
    ...selectedSx,
  };

  const mergedSx = (Array.isArray(sx) ? [baseSx, ...sx] : [baseSx, sx].filter(Boolean)) as SxProps<Theme>;

  return <Button {...props} variant={variant} disableElevation sx={mergedSx} />;
};
