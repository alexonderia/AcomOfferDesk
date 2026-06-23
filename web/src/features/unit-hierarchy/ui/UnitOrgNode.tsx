import AddOutlinedIcon from '@mui/icons-material/AddOutlined';
import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import GroupAddOutlinedIcon from '@mui/icons-material/GroupAddOutlined';
import MoreHorizOutlinedIcon from '@mui/icons-material/MoreHorizOutlined';
import { Box, Button, IconButton, Menu, MenuItem, Stack, Typography } from '@mui/material';
import { alpha } from '@mui/material/styles';
import { useState } from 'react';
import type { UnitMember, UnitNode } from '@shared/api/units';
import { OrgUserCard } from './OrgUserCard';
import {
  connectorLineSx,
  groupMembersForOrgChart,
  hierarchyPageColors,
} from './unitHierarchyStyles';

type UnitOrgNodeProps = {
  depth: number;
  onCreateChild?: ((unit: UnitNode) => void) | undefined;
  onDeactivate: (unit: UnitNode) => void;
  onDeleteMember: (unit: UnitNode, member: UnitMember) => void;
  onOpenMemberDialog?: ((unit: UnitNode) => void) | undefined;
  onRename: (unit: UnitNode) => void;
  showMembers?: boolean;
  showPrimaryActions?: boolean;
  unit: UnitNode;
};

const renderMemberRow = (
  members: UnitMember[],
  unit: UnitNode,
  canManageMembers: boolean,
  onDeleteMember: (unit: UnitNode, member: UnitMember) => void
) => (
  <Box sx={{ display: 'flex', gap: 1.4, justifyContent: 'center', width: 'max-content' }}>
    {members.map((member) => (
      <OrgUserCard
        key={`${unit.unit_id}-${member.user_id}`}
        canManageMembers={canManageMembers}
        member={member}
        onDelete={canManageMembers ? () => onDeleteMember(unit, member) : undefined}
        unitLabel={unit.name}
      />
    ))}
  </Box>
);

const getCreateChildActionLabel = () => 'Добавить дочерний узел';

export const UnitOrgNode = ({
  depth,
  onCreateChild,
  onDeactivate,
  onDeleteMember,
  onOpenMemberDialog,
  onRename,
  showMembers = true,
  showPrimaryActions = true,
  unit,
}: UnitOrgNodeProps) => {
  const [menuAnchorEl, setMenuAnchorEl] = useState<HTMLElement | null>(null);
  const canManageMembers = unit.actions.canManageMembers;
  const { contractors, leaders, team } = groupMembersForOrgChart(unit.members);
  const hasMenuActions = unit.actions.canUpdate || unit.actions.canDeactivate;
  const hasVisiblePrimaryActions = showPrimaryActions && (
    (unit.actions.canCreateChild && Boolean(onCreateChild))
    || (unit.actions.canManageMembers && Boolean(onOpenMemberDialog))
  );

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 'max-content' }}>
      <Stack spacing={showMembers ? 1.2 : 0} alignItems="center" sx={{ width: 'max-content' }}>
        <Stack
          direction="row"
          spacing={0.75}
          alignItems="center"
          sx={{
            minHeight: 34,
            borderRadius: 999,
            border: `1px solid ${alpha(hierarchyPageColors.cardBorder, 0.95)}`,
            backgroundColor: alpha('#ffffff', 0.88),
            px: 1.15,
            py: 0.55,
            boxShadow: '0 2px 8px rgba(27, 39, 57, 0.05)',
          }}
        >
          <Typography
            sx={{
              color: hierarchyPageColors.textPrimary,
              fontSize: 13.2,
              fontWeight: 600,
              lineHeight: 1.2,
              maxWidth: 320,
              overflowWrap: 'anywhere',
            }}
          >
            {unit.name}
          </Typography>
          {hasMenuActions ? (
            <>
              <IconButton
                size="small"
                onClick={(event) => setMenuAnchorEl(event.currentTarget)}
                sx={{
                  ml: 0.25,
                  width: 24,
                  height: 24,
                  color: alpha(hierarchyPageColors.textSecondary, 0.9),
                }}
              >
                <MoreHorizOutlinedIcon sx={{ fontSize: 17 }} />
              </IconButton>
              <Menu anchorEl={menuAnchorEl} open={Boolean(menuAnchorEl)} onClose={() => setMenuAnchorEl(null)}>
                {unit.actions.canUpdate ? (
                  <MenuItem
                    onClick={() => {
                      setMenuAnchorEl(null);
                      onRename(unit);
                    }}
                  >
                    <EditOutlinedIcon sx={{ mr: 1, fontSize: 18 }} />
                    Переименовать узел
                  </MenuItem>
                ) : null}
                {unit.actions.canDeactivate ? (
                  <MenuItem
                    onClick={() => {
                      setMenuAnchorEl(null);
                      onDeactivate(unit);
                    }}
                    sx={{ color: 'error.main' }}
                  >
                    <DeleteOutlineRoundedIcon sx={{ mr: 1, fontSize: 18 }} />
                    Деактивировать узел
                  </MenuItem>
                ) : null}
              </Menu>
            </>
          ) : null}
        </Stack>

        {hasVisiblePrimaryActions ? (
          <Stack direction="row" spacing={0.75} useFlexGap flexWrap="wrap" justifyContent="center" sx={{ maxWidth: 360 }}>
            {unit.actions.canCreateChild && onCreateChild ? (
              <Button
                size="small"
                variant="outlined"
                startIcon={<AddOutlinedIcon sx={{ fontSize: 16 }} />}
                onClick={() => onCreateChild(unit)}
                sx={{ minHeight: 28, px: 1.15, py: 0.25, borderRadius: 1.25, textTransform: 'none' }}
              >
                {getCreateChildActionLabel()}
              </Button>
            ) : null}
            {unit.actions.canManageMembers && onOpenMemberDialog ? (
              <Button
                size="small"
                variant="outlined"
                startIcon={<GroupAddOutlinedIcon sx={{ fontSize: 16 }} />}
                onClick={() => onOpenMemberDialog(unit)}
                sx={{ minHeight: 28, px: 1.15, py: 0.25, borderRadius: 1.25, textTransform: 'none' }}
              >
                Добавить сотрудника
              </Button>
            ) : null}
          </Stack>
        ) : null}

        {showMembers ? (
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'flex-start',
            }}
          >
            {leaders.length > 0 || team.length > 0 || contractors.length > 0 ? (
              <Stack spacing={1.2} alignItems="center" sx={{ width: 'max-content' }}>
                {leaders.length > 0 ? renderMemberRow(leaders, unit, canManageMembers, onDeleteMember) : null}
                {team.length > 0 ? renderMemberRow(team, unit, canManageMembers, onDeleteMember) : null}
                {contractors.length > 0 ? renderMemberRow(contractors, unit, canManageMembers, onDeleteMember) : null}
              </Stack>
            ) : (
              <Box
                sx={{
                  minWidth: 172,
                  borderRadius: 1.8,
                  border: `1px dashed ${alpha(hierarchyPageColors.canvasBorder, 0.95)}`,
                  backgroundColor: alpha('#ffffff', 0.76),
                  px: 1.25,
                  py: 1,
                }}
              >
                <Typography
                  variant="body2"
                  sx={{
                    color: hierarchyPageColors.textSecondary,
                    fontSize: 11.2,
                    textAlign: 'center',
                  }}
                >
                  В этом узле пока нет участников.
                </Typography>
              </Box>
            )}
          </Box>
        ) : null}
      </Stack>

      {unit.children.length > 0 ? (
        <Box sx={{ mt: 2.2, display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%' }}>
          <Box sx={{ ...connectorLineSx, width: '1px', height: '18px' }} />

          <Box sx={{ display: 'flex', gap: 1.8, alignItems: 'flex-start', justifyContent: 'center', width: 'max-content' }}>
            {unit.children.map((child, index) => {
              const isFirst = index === 0;
              const isLast = index === unit.children.length - 1;
              const hasManyChildren = unit.children.length > 1;

              return (
                <Box key={child.unit_id} sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 'max-content' }}>
                  {hasManyChildren ? (
                    <Box sx={{ position: 'relative', width: '100%', height: '20px', minWidth: 172 }}>
                      {!isFirst ? (
                        <Box
                          sx={{
                            ...connectorLineSx,
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            right: '50%',
                            height: '1px',
                          }}
                        />
                      ) : null}
                      {!isLast ? (
                        <Box
                          sx={{
                            ...connectorLineSx,
                            position: 'absolute',
                            top: 0,
                            left: '50%',
                            right: 0,
                            height: '1px',
                          }}
                        />
                      ) : null}
                      <Box
                        sx={{
                          ...connectorLineSx,
                          position: 'absolute',
                          top: 0,
                          left: '50%',
                          width: '1px',
                          height: '20px',
                          transform: 'translateX(-50%)',
                        }}
                      />
                    </Box>
                  ) : (
                    <Box sx={{ ...connectorLineSx, width: '1px', height: '20px' }} />
                  )}

                  <UnitOrgNode
                    depth={depth + 1}
                    onCreateChild={onCreateChild}
                    onDeactivate={onDeactivate}
                    onDeleteMember={onDeleteMember}
                    onOpenMemberDialog={onOpenMemberDialog}
                    onRename={onRename}
                    showMembers={showMembers}
                    showPrimaryActions={showPrimaryActions}
                    unit={child}
                  />
                </Box>
              );
            })}
          </Box>
        </Box>
      ) : null}
    </Box>
  );
};
