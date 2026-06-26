import AddOutlinedIcon from '@mui/icons-material/AddOutlined';
import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import GroupAddOutlinedIcon from '@mui/icons-material/GroupAddOutlined';
import MoreHorizOutlinedIcon from '@mui/icons-material/MoreHorizOutlined';
import {
  Box,
  Button,
  IconButton,
  Menu,
  MenuItem,
  Stack,
  Tooltip,
  Typography,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import { useState } from 'react';
import type { UnitNode } from '@shared/api/units';
import { ROLE } from '@shared/constants/roles';
import { PeopleFlatList, PeopleTree } from './PeopleTree';
import {
  connectorLineSx,
  hierarchyPageColors,
} from './unitHierarchyStyles';

type UnitOrgNodeProps = {
  depth: number;
  onCreateChild?: ((unit: UnitNode) => void) | undefined;
  onDelete: (unit: UnitNode) => void;
  onMoveMember?: ((unit: UnitNode, member: UnitNode['members'][number]) => void) | undefined;
  onOpenMemberDialog?: ((unit: UnitNode) => void) | undefined;
  onOpenUnitDetails?: ((unit: UnitNode) => void) | undefined;
  onRemoveMember?: ((unit: UnitNode, member: UnitNode['members'][number]) => void) | undefined;
  onRename: (unit: UnitNode) => void;
  showMembers?: boolean;
  showPrimaryActions?: boolean;
  unit: UnitNode;
};

export const UnitOrgNode = ({
  depth,
  onCreateChild,
  onDelete,
  onMoveMember,
  onOpenMemberDialog,
  onOpenUnitDetails,
  onRemoveMember,
  onRename,
  showMembers = true,
  showPrimaryActions = true,
  unit,
}: UnitOrgNodeProps) => {
  const [menuAnchorEl, setMenuAnchorEl] = useState<HTMLElement | null>(null);
  const hasMenuActions = unit.actions.canUpdate || unit.actions.canDelete;
  const canCreateChild = showPrimaryActions && unit.actions.canCreateChild && Boolean(onCreateChild);
  const canOpenMemberDialog = unit.actions.canManageMembers && Boolean(onOpenMemberDialog);
  const canOpenUnitDetails = Boolean(onOpenUnitDetails);
  const canManageMembers = unit.actions.canManageMembers;

  const staff = unit.members.filter((member) => member.role_id !== ROLE.CONTRACTOR);
  const contractors = unit.members.filter((member) => member.role_id === ROLE.CONTRACTOR);
  const hasChildren = unit.children.length > 0;

  const openUnitDetails = () => {
    onOpenUnitDetails?.(unit);
  };

  const renderChildNode = (child: UnitNode) => (
    <UnitOrgNode
      depth={depth + 1}
      onCreateChild={onCreateChild}
      onDelete={onDelete}
      onMoveMember={onMoveMember}
      onOpenMemberDialog={onOpenMemberDialog}
      onOpenUnitDetails={onOpenUnitDetails}
      onRemoveMember={onRemoveMember}
      onRename={onRename}
      showMembers={showMembers}
      showPrimaryActions={showPrimaryActions}
      unit={child}
    />
  );

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 'max-content' }}>
      <Box
        role={canOpenUnitDetails ? 'button' : undefined}
        aria-label={canOpenUnitDetails ? `Открыть состав объединения ${unit.name}` : undefined}
        tabIndex={canOpenUnitDetails ? 0 : undefined}
        onClick={canOpenUnitDetails ? openUnitDetails : undefined}
        onKeyDown={canOpenUnitDetails
          ? (event) => {
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault();
              openUnitDetails();
            }
          }
          : undefined}
        sx={{
          width: 332,
          maxWidth: 'min(332px, calc(100vw - 40px))',
          borderRadius: 2.5,
          border: `1px solid ${alpha(hierarchyPageColors.cardBorder, 0.98)}`,
          backgroundColor: '#ffffff',
          boxShadow: hierarchyPageColors.shadow,
          px: 1.4,
          py: 1.3,
          zIndex: 1,
          cursor: canOpenUnitDetails ? 'pointer' : 'default',
          transition: canOpenUnitDetails ? 'border-color 0.16s ease, box-shadow 0.16s ease' : undefined,
          '&:hover': canOpenUnitDetails ? {
            borderColor: alpha(hierarchyPageColors.connector, 0.38),
            boxShadow: '0 4px 12px rgba(15, 23, 42, 0.08)',
          } : undefined,
        }}
      >
        <Stack spacing={1.15}>
          <Stack direction="row" spacing={1} justifyContent="space-between" alignItems="flex-start">
            <Box sx={{ minWidth: 0 }}>
              <Typography
                sx={{
                  color: hierarchyPageColors.textPrimary,
                  fontSize: 15,
                  fontWeight: 700,
                  lineHeight: 1.24,
                  overflowWrap: 'anywhere',
                }}
              >
                {unit.name}
              </Typography>
            </Box>

            {hasMenuActions ? (
              <>
                <IconButton
                  size="small"
                  onClick={(event) => {
                    event.stopPropagation();
                    setMenuAnchorEl(event.currentTarget);
                  }}
                  sx={{
                    mt: -0.2,
                    mr: -0.35,
                    color: alpha(hierarchyPageColors.textSecondary, 0.92),
                  }}
                >
                  <MoreHorizOutlinedIcon sx={{ fontSize: 18 }} />
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
                      Изменить объединение
                    </MenuItem>
                  ) : null}
                  {unit.actions.canDelete ? (
                    <MenuItem
                      onClick={() => {
                        setMenuAnchorEl(null);
                        onDelete(unit);
                      }}
                      sx={{ color: 'error.main' }}
                    >
                      <DeleteOutlineRoundedIcon sx={{ mr: 1, fontSize: 18 }} />
                      Удалить объединение
                    </MenuItem>
                  ) : null}
                </Menu>
              </>
            ) : null}
          </Stack>

          <Stack direction="row" spacing={0.75} useFlexGap flexWrap="wrap">
            <Box
              sx={{
                borderRadius: 999,
                px: 1,
                py: 0.38,
                backgroundColor: alpha(hierarchyPageColors.softBlue, 0.08),
                color: hierarchyPageColors.softBlue,
                fontSize: 11.5,
                fontWeight: 700,
                lineHeight: 1.2,
              }}
            >
              Сотрудники: {staff.length}
            </Box>
            {contractors.length > 0 ? (
              <Box
                sx={{
                  borderRadius: 999,
                  px: 1,
                  py: 0.38,
                  backgroundColor: alpha(hierarchyPageColors.softPink, 0.08),
                  color: hierarchyPageColors.softPink,
                  fontSize: 11.5,
                  fontWeight: 700,
                  lineHeight: 1.2,
                }}
              >
                Контрагенты: {contractors.length}
              </Box>
            ) : null}
            <Box
              sx={{
                borderRadius: 999,
                px: 1,
                py: 0.38,
                backgroundColor: alpha(hierarchyPageColors.softTeal, 0.08),
                color: hierarchyPageColors.softTeal,
                fontSize: 11.5,
                fontWeight: 700,
                lineHeight: 1.2,
              }}
            >
              Дочерние объединения: {unit.children.length}
            </Box>
          </Stack>

          {showPrimaryActions && canOpenMemberDialog ? (
            <Button
              size="small"
              variant="outlined"
              startIcon={<GroupAddOutlinedIcon sx={{ fontSize: 16 }} />}
              onClick={(event) => {
                event.stopPropagation();
                onOpenMemberDialog?.(unit);
              }}
              sx={{ alignSelf: 'flex-start', minHeight: 30, px: 1.15, py: 0.25, borderRadius: 1.4, textTransform: 'none' }}
            >
              Добавить сотрудника
            </Button>
          ) : null}

          {showMembers ? (
            <Box
              sx={{
                borderTop: `1px solid ${alpha(hierarchyPageColors.canvasBorder, 0.9)}`,
                pt: 1,
              }}
              onClick={(event) => event.stopPropagation()}
            >
              <PeopleTree
                emptyLabel="Сотрудников пока нет."
                members={staff}
                onMove={canManageMembers && onMoveMember ? (member) => onMoveMember(unit, member) : undefined}
                onRemove={canManageMembers && onRemoveMember ? (member) => onRemoveMember(unit, member) : undefined}
                title="Состав"
              />
              {contractors.length > 0 ? (
                <Box sx={{ mt: 1 }}>
                  <PeopleFlatList emptyLabel="" members={contractors} title="Контрагенты" />
                </Box>
              ) : null}
            </Box>
          ) : null}
        </Stack>
      </Box>

      {(canCreateChild || hasChildren) ? (
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%' }}>
          <Box sx={{ ...connectorLineSx, width: '2px', height: '20px', mt: '-1px' }} />

          {canCreateChild ? (
            <>
              <Tooltip title="Добавить дочернее объединение">
                <IconButton
                  aria-label={`Добавить дочернее объединение в ${unit.name}`}
                  onClick={(event) => {
                    event.stopPropagation();
                    onCreateChild?.(unit);
                  }}
                  sx={{
                    width: 32,
                    height: 32,
                    bgcolor: 'primary.main',
                    color: '#ffffff',
                    boxShadow: hierarchyPageColors.shadow,
                    '&:hover': { bgcolor: 'primary.dark' },
                  }}
                >
                  <AddOutlinedIcon sx={{ fontSize: 20 }} />
                </IconButton>
              </Tooltip>
              {hasChildren ? <Box sx={{ ...connectorLineSx, width: '2px', height: '20px', mb: '-1px' }} /> : null}
            </>
          ) : null}

          {hasChildren ? (
            unit.children.length === 1 ? (
              renderChildNode(unit.children[0]!)
            ) : (
              <Box sx={{ display: 'flex', gap: 2.2, alignItems: 'flex-start', justifyContent: 'center', width: 'max-content' }}>
                {unit.children.map((child, index) => {
                  const isFirst = index === 0;
                  const isLast = index === unit.children.length - 1;

                  return (
                    <Box key={child.unit_id} sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 'max-content' }}>
                      <Box sx={{ position: 'relative', width: '100%', height: '20px', minWidth: 220 }}>
                        {!isFirst ? (
                          <Box sx={{ ...connectorLineSx, position: 'absolute', top: 0, left: 0, right: '50%', height: '2px' }} />
                        ) : null}
                        {!isLast ? (
                          <Box sx={{ ...connectorLineSx, position: 'absolute', top: 0, left: '50%', right: 0, height: '2px' }} />
                        ) : null}
                        <Box
                          sx={{
                            ...connectorLineSx,
                            position: 'absolute',
                            top: 0,
                            left: '50%',
                            width: '2px',
                            height: '21px',
                            transform: 'translateX(-50%)',
                          }}
                        />
                      </Box>
                      {renderChildNode(child)}
                    </Box>
                  );
                })}
              </Box>
            )
          ) : null}
        </Box>
      ) : null}
    </Box>
  );
};
