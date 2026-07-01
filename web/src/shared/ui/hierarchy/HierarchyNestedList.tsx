import { Box } from '@mui/material';
import type { ReactNode } from 'react';
import { hierarchyListRootSx, hierarchyNestedGroupSx } from './hierarchyListStyles';

type HierarchyNestedListProps = {
  children: ReactNode;
  nested?: boolean;
  role?: 'list' | 'group';
};

export const HierarchyNestedList = ({ children, nested = false, role = 'list' }: HierarchyNestedListProps) => (
  <Box
    component="ul"
    role={role}
    sx={nested ? hierarchyNestedGroupSx : hierarchyListRootSx}
  >
    {children}
  </Box>
);

type HierarchyNestedItemProps = {
  children?: ReactNode;
  content: ReactNode;
  nested?: ReactNode;
};

export const HierarchyNestedItem = ({ children, content, nested }: HierarchyNestedItemProps) => (
  <Box
    component="li"
    sx={{
      position: 'relative',
      listStyle: 'none',
      minWidth: 0,
    }}
  >
    {content}
    {nested}
    {children}
  </Box>
);

type HierarchyListDividerProps = {
  label?: string;
};

export const HierarchyListDivider = ({ label }: HierarchyListDividerProps) => (
  <Box
    component="li"
    role="separator"
    sx={{
      listStyle: 'none',
      py: 0.45,
    }}
  >
    {label ? (
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
        }}
      >
        <Box sx={{ flex: 1, height: '1px', bgcolor: 'divider' }} />
        <Box
          component="span"
          sx={{
            fontSize: 10,
            fontWeight: 600,
            letterSpacing: '0.04em',
            textTransform: 'uppercase',
            color: 'text.secondary',
            whiteSpace: 'nowrap',
          }}
        >
          {label}
        </Box>
        <Box sx={{ flex: 1, height: '1px', bgcolor: 'divider' }} />
      </Box>
    ) : (
      <Box sx={{ height: '1px', bgcolor: 'divider' }} />
    )}
  </Box>
);
