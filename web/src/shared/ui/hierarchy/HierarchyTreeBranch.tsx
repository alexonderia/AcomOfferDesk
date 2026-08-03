import { Box, useTheme } from '@mui/material';
import type { ReactNode } from 'react';
import {
  getHierarchyNestedGroupSx,
  HIERARCHY_LIST_COMPACT_BLOCK_GAP,
  type HierarchyGuideVariant,
} from './hierarchyThemeStyles';

type HierarchyTreeBranchProps = {
  children?: ReactNode;
  content?: ReactNode;
  variant?: HierarchyGuideVariant;
};

export const HierarchyTreeBranch = ({
  children,
  content,
  variant = 'tree',
}: HierarchyTreeBranchProps) => {
  const theme = useTheme();
  const nestedGroupSx = getHierarchyNestedGroupSx(theme, variant);
  const rootSx = variant === 'compact' && content && children
    ? {
      minWidth: 0,
      display: 'flex',
      flexDirection: 'column',
      gap: HIERARCHY_LIST_COMPACT_BLOCK_GAP,
    }
    : { minWidth: 0 };

  if (!children) {
    return <Box sx={rootSx}>{content}</Box>;
  }

  if (!content) {
    return (
      <Box sx={{ ...nestedGroupSx, minWidth: 0 }}>
        {children}
      </Box>
    );
  }

  return (
    <Box sx={rootSx}>
      {content}
      <Box sx={nestedGroupSx}>
        {children}
      </Box>
    </Box>
  );
};
