import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded';
import SwapHorizRoundedIcon from '@mui/icons-material/SwapHorizRounded';
import type { ReactNode } from 'react';
import { Box, IconButton, Stack, Tooltip, Typography } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import type { UnitMember } from '@shared/api/units';
import { buildPeopleTree, type PersonTreeNode } from '@shared/lib/hierarchy/buildPeopleTree';
import { HierarchyTreeBranch } from '@shared/ui/hierarchy/HierarchyTreeBranch';
import { HierarchyViewPersonRow } from '@shared/ui/hierarchy/HierarchyViewPersonRow';
import { getHierarchyEmptyStateSx } from '@shared/ui/hierarchy/hierarchyThemeStyles';
import type { HierarchyPersonVisual } from '@shared/ui/hierarchy/hierarchyPersonUtils';
import { HierarchyPeopleViewTree } from './HierarchyPeopleViewTree';
import { outlinedIconButtonSx } from './unitHierarchyStyles';

export type { PersonTreeNode } from '@shared/lib/hierarchy/buildPeopleTree';
export { buildPeopleTree } from '@shared/lib/hierarchy/buildPeopleTree';

const memberToPerson = (member: UnitMember): HierarchyPersonVisual => ({
  userId: member.user_id,
  fullName: member.full_name,
  roleName: member.role_name,
  status: member.status,
});

const MemberActions = ({
  member,
  onAssign,
  onMove,
  onRemove,
}: {
  member: UnitMember;
  onAssign?: ((member: UnitMember) => void) | undefined;
  onMove?: ((member: UnitMember) => void) | undefined;
  onRemove?: ((member: UnitMember) => void) | undefined;
}) => {
  if (!onAssign && !onMove && !onRemove) {
    return null;
  }

  const displayName = member.full_name?.trim() || member.user_id;

  return (
    <Stack direction="row" spacing={0.25}>
      {onAssign ? (
        <Tooltip title="Определить в подразделение">
          <IconButton size="small" onClick={() => onAssign(member)} aria-label={`Определить ${displayName} в подразделение`} sx={outlinedIconButtonSx}>
            <SwapHorizRoundedIcon sx={{ fontSize: 17 }} />
          </IconButton>
        </Tooltip>
      ) : null}
      {onMove ? (
        <Tooltip title="Переместить в другое объединение">
          <IconButton size="small" onClick={() => onMove(member)} aria-label={`Переместить ${displayName}`} sx={outlinedIconButtonSx}>
            <SwapHorizRoundedIcon sx={{ fontSize: 17 }} />
          </IconButton>
        </Tooltip>
      ) : null}
      {onRemove ? (
        <Tooltip title="Открепить от объединения">
          <IconButton size="small" onClick={() => onRemove(member)} aria-label={`Открепить ${displayName}`} sx={outlinedIconButtonSx}>
            <DeleteOutlineRoundedIcon sx={{ fontSize: 17 }} />
          </IconButton>
        </Tooltip>
      ) : null}
    </Stack>
  );
};

const ManagePersonRow = ({
  isRoot = false,
  member,
  onAssign,
  onMove,
  onRemove,
}: {
  isRoot?: boolean;
  member: UnitMember;
  onAssign?: ((member: UnitMember) => void) | undefined;
  onMove?: ((member: UnitMember) => void) | undefined;
  onRemove?: ((member: UnitMember) => void) | undefined;
}) => (
  <HierarchyViewPersonRow
    endAdornment={<MemberActions member={member} onAssign={onAssign} onMove={onMove} onRemove={onRemove} />}
    highlight={isRoot}
    person={memberToPerson(member)}
  />
);

const renderManageBranch = (
  node: PersonTreeNode,
  isRoot: boolean,
  onAssign?: ((member: UnitMember) => void) | undefined,
  onMove?: ((member: UnitMember) => void) | undefined,
  onRemove?: ((member: UnitMember) => void) | undefined,
) => (
  <HierarchyTreeBranch
    key={node.user_id}
    content={<ManagePersonRow isRoot={isRoot} member={node} onAssign={onAssign} onMove={onMove} onRemove={onRemove} />}
  >
    {node.children.length > 0
      ? node.children.map((child) => renderManageBranch(child, false, onAssign, onMove, onRemove))
      : null}
  </HierarchyTreeBranch>
);

const EmptyState = ({ label }: { label: string }) => {
  const theme = useTheme();

  return (
    <Box sx={getHierarchyEmptyStateSx(theme)}>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
    </Box>
  );
};

export const PeopleTree = ({
  emptyLabel,
  headerAction,
  hideHeader = false,
  members,
  onMove,
  onRemove,
  readonly = false,
  title,
}: {
  emptyLabel: string;
  headerAction?: ReactNode;
  hideHeader?: boolean;
  members: UnitMember[];
  onMove?: ((member: UnitMember) => void) | undefined;
  onRemove?: ((member: UnitMember) => void) | undefined;
  readonly?: boolean;
  title: string;
}) => {
  const isReadonly = readonly || (!onMove && !onRemove);
  const roots = buildPeopleTree(members);

  return (
    <Stack spacing={1} sx={{ minWidth: 0 }}>
      {hideHeader ? null : (
        <Stack direction="row" spacing={1} alignItems="center" justifyContent="space-between">
          <Stack direction="row" spacing={0.8} alignItems="center" sx={{ minWidth: 0 }}>
            <Typography sx={{ fontSize: 14, fontWeight: 600 }}>{title}</Typography>
            {headerAction}
          </Stack>
          {members.length > 0 ? (
            <Typography variant="caption" color="text.secondary">
              {members.length}
            </Typography>
          ) : null}
        </Stack>
      )}
      {roots.length === 0 ? (
        <EmptyState label={emptyLabel} />
      ) : isReadonly ? (
        <HierarchyPeopleViewTree emptyLabel={emptyLabel} members={members} />
      ) : (
        <>
          {roots.map((root) => renderManageBranch(root, true, undefined, onMove, onRemove))}
        </>
      )}
    </Stack>
  );
};

export const PeopleFlatList = ({
  emptyLabel,
  headerAction,
  hideHeader = false,
  members,
  onAssign,
  onRemove,
  readonly = false,
  title,
}: {
  emptyLabel: string;
  headerAction?: ReactNode;
  hideHeader?: boolean;
  members: UnitMember[];
  onAssign?: ((member: UnitMember) => void) | undefined;
  onRemove?: ((member: UnitMember) => void) | undefined;
  readonly?: boolean;
  title: string;
}) => {
  const isReadonly = readonly || (!onAssign && !onRemove);

  return (
    <Stack spacing={1} sx={{ minWidth: 0 }}>
      {hideHeader ? null : (
        <Stack direction="row" spacing={1} alignItems="center" justifyContent="space-between">
          <Stack direction="row" spacing={0.8} alignItems="center" sx={{ minWidth: 0 }}>
            <Typography sx={{ fontSize: 14, fontWeight: 600 }}>{title}</Typography>
            {headerAction}
          </Stack>
          {members.length > 0 ? (
            <Typography variant="caption" color="text.secondary">
              {members.length}
            </Typography>
          ) : null}
        </Stack>
      )}
      {members.length === 0 ? (
        <EmptyState label={emptyLabel} />
      ) : isReadonly ? (
        <Stack spacing={0.15}>
          {members.map((member) => (
            <HierarchyViewPersonRow key={member.user_id} highlight person={memberToPerson(member)} />
          ))}
        </Stack>
      ) : (
        <Stack spacing={0.15}>
          {members.map((member) => (
            <ManagePersonRow key={member.user_id} member={member} onAssign={onAssign} onRemove={onRemove} />
          ))}
        </Stack>
      )}
    </Stack>
  );
};
