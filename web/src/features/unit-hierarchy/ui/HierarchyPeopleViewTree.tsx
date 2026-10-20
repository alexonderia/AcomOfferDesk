import type { ReactNode } from 'react';
import { Box, Typography } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import type { UnitMember } from '@shared/api/units';
import { buildPeopleTree, type PersonTreeNode } from '@shared/lib/hierarchy/buildPeopleTree';
import { HierarchyTreeBranch } from '@shared/ui/hierarchy/HierarchyTreeBranch';
import { HierarchyViewPersonRow } from '@shared/ui/hierarchy/HierarchyViewPersonRow';
import { getHierarchyEmptyStateSx } from '@shared/ui/hierarchy/hierarchyThemeStyles';
import type { HierarchyPersonTone, HierarchyPersonVisual } from '@shared/ui/hierarchy/hierarchyPersonUtils';

const memberToPerson = (member: UnitMember): HierarchyPersonVisual => ({
  userId: member.user_id,
  fullName: member.full_name,
  roleName: member.role_name,
  status: member.status,
});

const PersonTreeNodeView = ({
  highlight = false,
  node,
  renderMeta,
  resolveTooltipTitle,
  resolveTone,
  resolveHighlight,
}: {
  highlight?: boolean;
  node: PersonTreeNode;
  renderMeta?: (person: HierarchyPersonVisual) => ReactNode;
  resolveTooltipTitle?: (person: HierarchyPersonVisual) => ReactNode;
  resolveTone?: (person: HierarchyPersonVisual) => HierarchyPersonTone;
  resolveHighlight?: (person: HierarchyPersonVisual) => boolean;
}) => {
  const person = memberToPerson(node);

  return (
    <HierarchyTreeBranch
      content={(
        <HierarchyViewPersonRow
          highlight={resolveHighlight?.(person) ?? highlight}
          meta={renderMeta?.(person)}
          person={person}
          tone={resolveTone?.(person)}
          tooltipTitle={resolveTooltipTitle?.(person)}
        />
      )}
    >
      {node.children.length > 0
        ? node.children.map((child) => (
          <PersonTreeNodeView
            key={child.user_id}
            node={child}
            renderMeta={renderMeta}
            resolveHighlight={resolveHighlight}
            resolveTone={resolveTone}
            resolveTooltipTitle={resolveTooltipTitle}
          />
        ))
        : null}
    </HierarchyTreeBranch>
  );
};

export const HierarchyPeopleViewTree = ({
  highlightRoots = true,
  members,
  roots,
  renderMeta,
  resolveTooltipTitle,
  resolveTone,
  resolveHighlight,
}: {
  emptyLabel?: string;
  highlightRoots?: boolean;
  members: UnitMember[];
  roots?: PersonTreeNode[];
  renderMeta?: (person: HierarchyPersonVisual) => ReactNode;
  resolveTooltipTitle?: (person: HierarchyPersonVisual) => ReactNode;
  resolveTone?: (person: HierarchyPersonVisual) => HierarchyPersonTone;
  resolveHighlight?: (person: HierarchyPersonVisual) => boolean;
}) => {
  const treeRoots = roots ?? buildPeopleTree(members);

  if (treeRoots.length === 0) {
    return null;
  }

  return (
    <>
      {treeRoots.map((root) => (
        <PersonTreeNodeView
          key={root.user_id}
          highlight={highlightRoots}
          node={root}
          renderMeta={renderMeta}
          resolveHighlight={resolveHighlight}
          resolveTone={resolveTone}
          resolveTooltipTitle={resolveTooltipTitle}
        />
      ))}
    </>
  );
};

export const HierarchyPeopleEmptyState = ({ label }: { label: string }) => {
  const theme = useTheme();

  return (
    <Box sx={getHierarchyEmptyStateSx(theme)}>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
    </Box>
  );
};
