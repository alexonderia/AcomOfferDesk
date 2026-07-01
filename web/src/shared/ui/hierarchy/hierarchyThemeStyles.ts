import { alpha, type Theme } from '@mui/material/styles';
import type { HierarchyPersonTone } from './hierarchyPersonUtils';

export const HIERARCHY_LIST_INDENT_PX = 20;
export const HIERARCHY_LIST_COMPACT_INDENT_PX = 12;
export const HIERARCHY_LIST_COMPACT_BLOCK_GAP = 1.25;
export const HIERARCHY_LIST_ROW_MIN_HEIGHT = 48;

export type HierarchyGuideVariant = 'tree' | 'compact';

export const getHierarchyGuideColor = (theme: Theme) => theme.palette.divider;

export const getHierarchyNestedGroupSx = (
  theme: Theme,
  variant: HierarchyGuideVariant = 'tree',
) => {
  if (variant === 'compact') {
    return {
      ml: `${HIERARCHY_LIST_COMPACT_INDENT_PX}px`,
      pl: `${HIERARCHY_LIST_COMPACT_INDENT_PX}px`,
      display: 'flex',
      flexDirection: 'column',
      gap: HIERARCHY_LIST_COMPACT_BLOCK_GAP,
      borderLeft: `1px solid ${alpha(theme.palette.primary.main, 0.18)}`,
      minWidth: 0,
    } as const;
  }

  const guideColor = getHierarchyGuideColor(theme);
  const maskColor = theme.palette.background.paper;

  return {
    ml: `${HIERARCHY_LIST_INDENT_PX / 2}px`,
    pl: `${HIERARCHY_LIST_INDENT_PX / 2}px`,
    borderLeft: `1px solid ${guideColor}`,
    '& > *': {
      position: 'relative',
    },
    '& > *::before': {
      content: '""',
      position: 'absolute',
      left: `-${HIERARCHY_LIST_INDENT_PX / 2 + 1}px`,
      top: HIERARCHY_LIST_ROW_MIN_HEIGHT / 2,
      width: `${HIERARCHY_LIST_INDENT_PX / 2}px`,
      height: '1px',
      bgcolor: guideColor,
    },
    '& > *:last-child::after': {
      content: '""',
      position: 'absolute',
      left: `-${HIERARCHY_LIST_INDENT_PX / 2 + 2}px`,
      top: HIERARCHY_LIST_ROW_MIN_HEIGHT / 2 + 1,
      bottom: 0,
      width: '4px',
      bgcolor: maskColor,
      zIndex: 1,
    },
  } as const;
};

const getHierarchyToneColor = (theme: Theme, tone: HierarchyPersonTone) => {
  if (tone === 'manager') {
    return theme.palette.primary.main;
  }
  if (tone === 'subordinate') {
    return theme.palette.success.main;
  }
  if (tone === 'self') {
    return theme.palette.info.main;
  }
  return theme.palette.primary.main;
};

export const getHierarchyPersonRowSx = (
  theme: Theme,
  highlight = false,
  tone: HierarchyPersonTone = 'default',
) => {
  const toneColor = getHierarchyToneColor(theme, tone);

  return ({
  display: 'flex',
  alignItems: 'center',
  gap: 1,
  minHeight: HIERARCHY_LIST_ROW_MIN_HEIGHT,
  minWidth: 0,
  px: 1.2,
  py: 0.7,
  mb: 0.35,
  borderRadius: `${theme.acomShape.controlRadius}px`,
  bgcolor: highlight
    ? alpha(toneColor, 0.1)
    : tone === 'default'
      ? theme.palette.background.paper
      : alpha(toneColor, 0.045),
  border: '1px solid',
  borderColor: highlight
    ? alpha(toneColor, 0.28)
    : tone === 'default'
      ? theme.palette.divider
      : alpha(toneColor, 0.2),
  boxShadow: `0 2px 8px ${alpha(theme.palette.common.black, 0.035)}`,
  transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
  });
};

export const getHierarchyDetailsPanelSx = (theme: Theme) => ({
  mx: 0.2,
  mb: 0.45,
  px: 1.1,
  py: 0.85,
  borderRadius: `${theme.acomShape.controlRadius}px`,
  bgcolor: theme.palette.brand.softSection,
  border: `1px solid ${theme.palette.divider}`,
});

export const getHierarchyEmptyStateSx = (theme: Theme) => ({
  borderRadius: `${theme.acomShape.controlRadius}px`,
  border: '1px dashed',
  borderColor: theme.palette.divider,
  backgroundColor: theme.palette.brand.softSection,
  px: 1.25,
  py: 1.1,
});

export const getHierarchyStatusColor = (theme: Theme, status: string) => {
  if (status === 'active') {
    return theme.palette.success.main;
  }
  if (status === 'review') {
    return theme.palette.warning.main;
  }
  if (status === 'blacklist') {
    return theme.palette.error.main;
  }
  return theme.palette.text.disabled;
};

export const getHierarchyAvatarSx = (
  theme: Theme,
  highlight = false,
  tone: HierarchyPersonTone = 'default',
) => {
  const toneColor = getHierarchyToneColor(theme, tone);

  return ({
  width: 36,
  height: 36,
  fontSize: 13,
  fontWeight: 700,
  bgcolor: highlight
    ? alpha(toneColor, 0.16)
    : alpha(toneColor, 0.1),
  color: toneColor,
  flexShrink: 0,
  border: `1px solid ${alpha(toneColor, highlight ? 0.28 : 0.18)}`,
  });
};

export const getHierarchyTreeControlButtonSx = (theme: Theme) => ({
  width: 32,
  height: 32,
  borderRadius: `${theme.acomShape.controlRadius}px`,
  border: `1px solid ${alpha(theme.palette.primary.main, 0.34)}`,
  color: theme.palette.primary.main,
  bgcolor: theme.palette.background.paper,
  '&:hover': {
    bgcolor: alpha(theme.palette.primary.main, 0.06),
    borderColor: alpha(theme.palette.primary.main, 0.58),
  },
});
