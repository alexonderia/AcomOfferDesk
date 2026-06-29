import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded';
import SwapHorizRoundedIcon from '@mui/icons-material/SwapHorizRounded';
import type { ReactNode } from 'react';
import { Avatar, Box, IconButton, Stack, Tooltip, Typography } from '@mui/material';
import { alpha } from '@mui/material/styles';
import type { UnitMember } from '@shared/api/units';
import {
  getMemberAccentColor,
  hierarchyPageColors,
  isPlaceholderPersonName,
  outlinedIconButtonSx,
  statusLabelByCode,
} from './unitHierarchyStyles';

export type PersonTreeNode = UnitMember & { children: PersonTreeNode[] };

const statusColorByCode: Record<string, string> = {
  active: '#16a34a',
  inactive: '#9ca3af',
  review: '#d97706',
  blacklist: '#dc2626',
};

const getDisplayName = (member: UnitMember): string => {
  const name = member.full_name?.trim();
  if (!name) {
    return member.user_id;
  }
  if (isPlaceholderPersonName(name)) {
    return 'Вакансия';
  }
  return name;
};

const getInitials = (member: UnitMember): string => {
  const name = member.full_name?.trim();
  if (name && !isPlaceholderPersonName(name)) {
    const parts = name.split(/\s+/).filter(Boolean);
    const initials = `${parts[0]?.[0] ?? ''}${parts.length > 1 ? parts[1]![0] : ''}`;
    if (initials) {
      return initials.toUpperCase();
    }
  }
  return (member.user_id || '?').slice(0, 2).toUpperCase();
};

export const buildPeopleTree = (members: UnitMember[]): PersonTreeNode[] => {
  const nodes = new Map<string, PersonTreeNode>(
    members.map((member) => [member.user_id, { ...member, children: [] }])
  );
  const childIds = new Set<string>();

  members.forEach((member) => {
    const parentId = member.id_parent_user;
    if (parentId && parentId !== member.user_id && nodes.has(parentId)) {
      nodes.get(parentId)!.children.push(nodes.get(member.user_id)!);
      childIds.add(member.user_id);
    }
  });

  const sortNodes = (list: PersonTreeNode[]) => {
    list.sort((left, right) =>
      getDisplayName(left).localeCompare(getDisplayName(right), 'ru')
    );
    list.forEach((node) => sortNodes(node.children));
  };

  let roots = members
    .filter((member) => !childIds.has(member.user_id))
    .map((member) => nodes.get(member.user_id)!);

  // Fallback for pathological cycles: never drop members.
  if (roots.length === 0 && members.length > 0) {
    roots = members.map((member) => ({ ...member, children: [] }));
  }

  sortNodes(roots);
  return roots;
};

export const PersonRow = ({
  member,
  onMove,
  onRemove,
}: {
  member: UnitMember;
  onMove?: ((member: UnitMember) => void) | undefined;
  onRemove?: ((member: UnitMember) => void) | undefined;
}) => {
  const accent = getMemberAccentColor(member.role_name);
  const statusColor = statusColorByCode[member.status] ?? hierarchyPageColors.textSecondary;

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1,
        minWidth: 0,
        borderRadius: 2,
        border: `1px solid ${alpha(hierarchyPageColors.canvasBorder, 0.9)}`,
        backgroundColor: '#ffffff',
        px: 1,
        py: 0.75,
      }}
    >
      <Avatar
        sx={{
          width: 34,
          height: 34,
          fontSize: 13,
          fontWeight: 700,
          bgcolor: alpha(accent, 0.14),
          color: accent,
          flexShrink: 0,
        }}
      >
        {getInitials(member)}
      </Avatar>

      <Box sx={{ minWidth: 0, flex: 1 }}>
        <Typography
          sx={{ fontSize: 13.5, fontWeight: 700, lineHeight: 1.2, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}
          title={getDisplayName(member)}
        >
          {getDisplayName(member)}
        </Typography>
        <Stack direction="row" spacing={0.6} alignItems="center" sx={{ mt: 0.1, minWidth: 0 }}>
          <Tooltip title={statusLabelByCode[member.status] ?? member.status}>
            <Box sx={{ width: 7, height: 7, borderRadius: '50%', bgcolor: statusColor, flexShrink: 0 }} />
          </Tooltip>
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}
            title={member.role_name}
          >
            {member.role_name}
          </Typography>
        </Stack>
      </Box>

      {(onMove || onRemove) ? (
        <Stack direction="row" spacing={0.25} sx={{ flexShrink: 0 }}>
          {onMove ? (
            <Tooltip title="Переместить в другое объединение">
              <IconButton size="small" onClick={() => onMove(member)} aria-label={`Переместить ${getDisplayName(member)}`} sx={outlinedIconButtonSx}>
                <SwapHorizRoundedIcon sx={{ fontSize: 17 }} />
              </IconButton>
            </Tooltip>
          ) : null}
          {onRemove ? (
            <Tooltip title="Открепить от объединения">
              <IconButton size="small" onClick={() => onRemove(member)} aria-label={`Открепить ${getDisplayName(member)}`} sx={outlinedIconButtonSx}>
                <DeleteOutlineRoundedIcon sx={{ fontSize: 17 }} />
              </IconButton>
            </Tooltip>
          ) : null}
        </Stack>
      ) : null}
    </Box>
  );
};

const PersonTreeBranch = ({
  depth,
  node,
  onMove,
  onRemove,
}: {
  depth: number;
  node: PersonTreeNode;
  onMove?: ((member: UnitMember) => void) | undefined;
  onRemove?: ((member: UnitMember) => void) | undefined;
}) => (
  <Box sx={{ minWidth: 0 }}>
    <PersonRow member={node} onMove={onMove} onRemove={onRemove} />
    {node.children.length > 0 ? (
      <Box
        sx={{
          mt: 0.6,
          ml: { xs: 1.25, sm: 2 },
          pl: { xs: 1, sm: 1.5 },
          borderLeft: `2px solid ${alpha(hierarchyPageColors.connector, 0.35)}`,
          display: 'flex',
          flexDirection: 'column',
          gap: 0.6,
        }}
      >
        {node.children.map((child) => (
          <PersonTreeBranch key={child.user_id} depth={depth + 1} node={child} onMove={onMove} onRemove={onRemove} />
        ))}
      </Box>
    ) : null}
  </Box>
);

const EmptyState = ({ label }: { label: string }) => (
  <Box
    sx={{
      borderRadius: 2,
      border: '1px dashed',
      borderColor: alpha(hierarchyPageColors.canvasBorder, 0.88),
      backgroundColor: alpha(hierarchyPageColors.canvas, 0.72),
      px: 1.25,
      py: 1.1,
    }}
  >
    <Typography variant="body2" color="text.secondary">
      {label}
    </Typography>
  </Box>
);

export const PeopleTree = ({
  emptyLabel,
  headerAction,
  members,
  onMove,
  onRemove,
  title,
}: {
  emptyLabel: string;
  headerAction?: ReactNode;
  members: UnitMember[];
  onMove?: ((member: UnitMember) => void) | undefined;
  onRemove?: ((member: UnitMember) => void) | undefined;
  title: string;
}) => {
  const roots = buildPeopleTree(members);

  return (
    <Stack spacing={1} sx={{ minWidth: 0 }}>
      <Stack direction="row" spacing={1} alignItems="center" justifyContent="space-between">
        <Stack direction="row" spacing={0.8} alignItems="center" sx={{ minWidth: 0 }}>
          <Typography sx={{ fontSize: 13.5, fontWeight: 800 }}>{title}</Typography>
          {headerAction}
        </Stack>
        {members.length > 0 ? (
          <Typography variant="caption" color="text.secondary">
            {members.length}
          </Typography>
        ) : null}
      </Stack>
      {roots.length === 0 ? (
        <EmptyState label={emptyLabel} />
      ) : (
        <Stack spacing={0.6} sx={{ minWidth: 0 }}>
          {roots.map((root) => (
            <PersonTreeBranch key={root.user_id} depth={0} node={root} onMove={onMove} onRemove={onRemove} />
          ))}
        </Stack>
      )}
    </Stack>
  );
};

export const PeopleFlatList = ({
  emptyLabel,
  headerAction,
  members,
  onRemove,
  title,
}: {
  emptyLabel: string;
  headerAction?: ReactNode;
  members: UnitMember[];
  onRemove?: ((member: UnitMember) => void) | undefined;
  title: string;
}) => (
  <Stack spacing={1} sx={{ minWidth: 0 }}>
    <Stack direction="row" spacing={1} alignItems="center" justifyContent="space-between">
      <Stack direction="row" spacing={0.8} alignItems="center" sx={{ minWidth: 0 }}>
        <Typography sx={{ fontSize: 13.5, fontWeight: 800 }}>{title}</Typography>
        {headerAction}
      </Stack>
      {members.length > 0 ? (
        <Typography variant="caption" color="text.secondary">
          {members.length}
        </Typography>
      ) : null}
    </Stack>
    {members.length === 0 ? (
      <EmptyState label={emptyLabel} />
    ) : (
      <Stack spacing={0.6} sx={{ minWidth: 0 }}>
        {members.map((member) => (
          <PersonRow key={member.user_id} member={member} onRemove={onRemove} />
        ))}
      </Stack>
    )}
  </Stack>
);

