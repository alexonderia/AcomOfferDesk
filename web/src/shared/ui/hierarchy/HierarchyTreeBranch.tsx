import { Box, useTheme } from '@mui/material';
import type { ReactNode } from 'react';
import { getHierarchyNestedGroupSx } from './hierarchyThemeStyles';

type HierarchyTreeBranchProps = {
  children?: ReactNode;
  content?: ReactNode;
};

export const HierarchyTreeBranch = ({
  children,
  content,
}: HierarchyTreeBranchProps) => {
  const theme = useTheme();
  const nestedGroupSx = getHierarchyNestedGroupSx(theme);

  if (!children) {
    return <Box sx={{ minWidth: 0 }}>{content}</Box>;
  }

  if (!content) {
    return (
      <Box sx={{ ...nestedGroupSx, minWidth: 0 }}>
        {children}
      </Box>
    );
  }

  return (
    <Box sx={{ minWidth: 0 }}>
      {content}
      <Box sx={nestedGroupSx}>
        {children}
      </Box>
    </Box>
  );
};
