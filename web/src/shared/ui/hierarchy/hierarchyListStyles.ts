import { HIERARCHY_LIST_INDENT_PX } from './hierarchyThemeStyles';

export { HIERARCHY_LIST_INDENT_PX };

export const hierarchyListRootSx = {
  listStyle: 'none',
  m: 0,
  p: 0,
  minWidth: 0,
} as const;

export const hierarchyNestedGroupSx = {
  listStyle: 'none',
  m: 0,
  mt: 0.1,
  mb: 0.1,
  ml: `${HIERARCHY_LIST_INDENT_PX}px`,
  pl: 1.25,
  minWidth: 0,
} as const;
