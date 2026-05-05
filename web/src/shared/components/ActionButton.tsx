import NavigateBeforeRounded from '@mui/icons-material/NavigateBeforeRounded';
import NavigateNextRounded from '@mui/icons-material/NavigateNextRounded';
import Button from '@mui/material/Button';
import type { ButtonProps } from '@mui/material/Button';
import { alpha, useTheme } from '@mui/material/styles';
import type { SxProps, Theme } from '@mui/material/styles';

export type ActionButtonVisualState = 'default' | 'hover' | 'pressed' | 'selected' | 'disabled';
export type ActionButtonKind = 'filled' | 'outlined' | 'custom';

type ActionButtonProps = Omit<ButtonProps, 'variant'> & {
  kind?: ActionButtonKind;
  selected?: boolean;
  visualState?: ActionButtonVisualState;
  showNavigationIcons?: boolean;
};

const resolveVariant = (kind: ActionButtonKind): NonNullable<ButtonProps['variant']> =>
  kind === 'filled' ? 'contained' : 'outlined';

const getRegularForcedStateSx = (
  theme: Theme,
  kind: Exclude<ActionButtonKind, 'custom'>,
  state: Exclude<ActionButtonVisualState, 'default' | 'disabled'>
): SxProps<Theme> => {
  const { primary, brand } = theme.palette;

  if (kind === 'filled') {
    const backgroundColor = state === 'hover' ? brand.primaryHover : state === 'selected' ? primary.main : brand.primaryPressed;

    return {
      backgroundColor,
      color: primary.contrastText,
      '&:hover': {
        backgroundColor,
      },
    };
  }

  const borderColor = state === 'hover' ? brand.primaryHover : state === 'selected' ? primary.main : brand.primaryPressed;
  const backgroundColor = state === 'hover' ? alpha(primary.main, 0.06) : alpha(primary.main, 0.12);

  return {
    borderColor,
    backgroundColor,
    color: primary.main,
    '&:hover': {
      borderColor,
      backgroundColor,
    },
  };
};

const getCustomBaseSx = (theme: Theme, selected: boolean, isDisabled: boolean): SxProps<Theme> => {
  const { primary, brand } = theme.palette;

  if (isDisabled) {
    return {
      borderColor: 'transparent',
      backgroundColor: 'transparent',
      color: brand.disabledText,
      '&.Mui-disabled': {
        borderColor: 'transparent',
        backgroundColor: 'transparent',
        color: brand.disabledText,
      },
    };
  }

  if (selected) {
    return {
      backgroundColor: primary.main,
      borderColor: primary.main,
      color: primary.contrastText,
      '&:hover': {
        backgroundColor: theme.palette.background.paper,
        borderColor: primary.main,
        color: primary.main,
        transition: 'background-color 0.28s ease, border-color 0.28s ease, color 0.28s ease',
      },
      '&:active': {
        backgroundColor: brand.primaryPressed,
        borderColor: brand.primaryPressed,
        color: primary.contrastText,
      },
    };
  }

  return {
    borderColor: 'transparent',
    backgroundColor: 'transparent',
    color: primary.main,
    '&:hover': {
      borderColor: primary.main,
      backgroundColor: alpha(primary.main, 0.04),
    },
    '&:active': {
      borderColor: brand.primaryPressed,
      backgroundColor: brand.primaryPressed,
      color: primary.contrastText,
    },
  };
};

const getCustomForcedStateSx = (
  theme: Theme,
  state: ActionButtonVisualState
): SxProps<Theme> | undefined => {
  const { primary, brand } = theme.palette;

  if (state === 'default') {
    return {
      borderColor: 'transparent',
      backgroundColor: 'transparent',
      color: primary.main,
      '&:hover': {
        borderColor: 'transparent',
        backgroundColor: 'transparent',
      },
    };
  }

  if (state === 'hover') {
    return {
      borderColor: primary.main,
      backgroundColor: alpha(primary.main, 0.04),
      color: primary.main,
      '&:hover': {
        borderColor: primary.main,
        backgroundColor: alpha(primary.main, 0.04),
      },
    };
  }

  if (state === 'pressed') {
    return {
      borderColor: brand.primaryPressed,
      backgroundColor: brand.primaryPressed,
      color: primary.contrastText,
      '&:hover': {
        borderColor: brand.primaryPressed,
        backgroundColor: brand.primaryPressed,
      },
    };
  }

  if (state === 'selected') {
    return {
      borderColor: primary.main,
      backgroundColor: primary.main,
      color: primary.contrastText,
      '&:hover': {
        borderColor: primary.main,
        backgroundColor: theme.palette.background.paper,
        color: primary.main,
      },
    };
  }

  return undefined;
};

const mergeSx = (stateSx: SxProps<Theme> | undefined, incomingSx: ButtonProps['sx']): SxProps<Theme> | undefined => {
  const sxParts: SxProps<Theme>[] = [];

  if (stateSx) {
    sxParts.push(stateSx);
  }

  if (Array.isArray(incomingSx)) {
    sxParts.push(...incomingSx);
  } else if (incomingSx) {
    sxParts.push(incomingSx);
  }

  return sxParts.length > 0 ? (sxParts as SxProps<Theme>) : undefined;
};

export const ActionButton = ({
  kind = 'filled',
  selected = false,
  visualState,
  disabled,
  sx,
  startIcon,
  endIcon,
  showNavigationIcons = true,
  ...props
}: ActionButtonProps) => {
  const theme = useTheme();
  const isDisabled = visualState === 'disabled' || Boolean(disabled);
  const resolvedVariant = resolveVariant(kind);
  const resolvedStartIcon = startIcon ?? (showNavigationIcons ? <NavigateBeforeRounded /> : undefined);
  const resolvedEndIcon = endIcon ?? (showNavigationIcons ? <NavigateNextRounded /> : undefined);

  const stateSx =
    kind === 'custom'
      ? visualState && visualState !== 'disabled'
        ? getCustomForcedStateSx(theme, visualState)
        : getCustomBaseSx(theme, selected, isDisabled)
      : visualState && visualState !== 'default' && visualState !== 'disabled'
      ? getRegularForcedStateSx(theme, kind, visualState)
      : undefined;

  return (
    <Button
      startIcon={resolvedStartIcon}
      endIcon={resolvedEndIcon}
      variant={resolvedVariant}
      disabled={isDisabled}
      sx={mergeSx(stateSx, sx)}
      {...props}
    />
  );
};
