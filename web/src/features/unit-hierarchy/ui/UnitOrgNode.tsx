import AddRoundedIcon from '@mui/icons-material/AddRounded';
import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded';
import GroupAddOutlinedIcon from '@mui/icons-material/GroupAddOutlined';
import {
  Box,
  IconButton,
  Stack,
  Tooltip,
  Typography,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import type { UnitNode } from '@shared/api/units';
import { ROLE } from '@shared/constants/roles';
import { PeopleFlatList, PeopleTree } from './PeopleTree';
import {
  connectorLineSx,
  hierarchyPageColors,
  orgNodeCardSx,
  orgNodeLayout,
  outlinedIconButtonSx,
} from './unitHierarchyStyles';
import { buildChildrenRowLayout, measureUnitSubtreeWidth } from './orgNodeLayoutUtils';

type UnitOrgNodeProps = {
  depth: number;
  onDelete: (unit: UnitNode) => void;
  onOpenCreateChildDialog?: ((unit: UnitNode) => void) | undefined;
  onMoveMember?: ((unit: UnitNode, member: UnitNode['members'][number]) => void) | undefined;
  onOpenMemberDialog?: ((unit: UnitNode) => void) | undefined;
  onOpenUnitDetails?: ((unit: UnitNode) => void) | undefined;
  onRemoveMember?: ((unit: UnitNode, member: UnitNode['members'][number]) => void) | undefined;
  showMembers?: boolean;
  showPrimaryActions?: boolean;
  unit: UnitNode;
};

export const UnitOrgNode = ({
  depth,
  onDelete,
  onOpenCreateChildDialog,
  onMoveMember,
  onOpenMemberDialog,
  onOpenUnitDetails,
  onRemoveMember,
  showMembers = true,
  showPrimaryActions = true,
  unit,
}: UnitOrgNodeProps) => {
  const canDelete = unit.actions.canDelete;
  const canCreateChild = showPrimaryActions && unit.actions.canCreateChild && Boolean(onOpenCreateChildDialog);
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
      onDelete={onDelete}
      onOpenCreateChildDialog={onOpenCreateChildDialog}
      onMoveMember={onMoveMember}
      onOpenMemberDialog={onOpenMemberDialog}
      onOpenUnitDetails={onOpenUnitDetails}
      onRemoveMember={onRemoveMember}
      showMembers={showMembers}
      showPrimaryActions={showPrimaryActions}
      unit={child}
    />
  );

  const childCount = unit.children.length;
  const stemHeight = orgNodeLayout.connectorHeight;
  const subtreeWidth = measureUnitSubtreeWidth(unit);

  const renderChildrenRow = () => {
    if (childCount === 0) {
      return null;
    }

    if (childCount === 1) {
      const childWidth = measureUnitSubtreeWidth(unit.children[0]!);
      return (
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: subtreeWidth }}>
          <Box sx={{ ...connectorLineSx, width: '2px', height: `${stemHeight}px` }} />
          <Box sx={{ width: childWidth, display: 'flex', justifyContent: 'center' }}>
            {renderChildNode(unit.children[0]!)}
          </Box>
        </Box>
      );
    }

    const { childCenters, childWidths, rowWidth } = buildChildrenRowLayout(unit.children);
    const firstCenter = childCenters[0] ?? 0;
    const lastCenter = childCenters[childCenters.length - 1] ?? 0;

    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: subtreeWidth }}>
        <Box
          sx={{
            position: 'relative',
            width: rowWidth,
            height: `${stemHeight}px`,
          }}
        >
          <Box
            sx={{
              ...connectorLineSx,
              position: 'absolute',
              top: 0,
              left: firstCenter,
              width: Math.max(0, lastCenter - firstCenter),
              height: '2px',
            }}
          />
          {unit.children.map((child, index) => (
            <Box
              key={child.unit_id}
              sx={{
                ...connectorLineSx,
                position: 'absolute',
                top: 0,
                left: childCenters[index],
                width: '2px',
                height: `${stemHeight}px`,
                transform: 'translateX(-50%)',
              }}
            />
          ))}
        </Box>
        <Box
          sx={{
            display: 'flex',
            gap: `${orgNodeLayout.childGap}px`,
            alignItems: 'flex-start',
            justifyContent: 'center',
            width: rowWidth,
          }}
        >
          {unit.children.map((child, index) => (
            <Box
              key={child.unit_id}
              sx={{
                width: childWidths[index],
                flex: `0 0 ${childWidths[index]}px`,
                display: 'flex',
                justifyContent: 'center',
              }}
            >
              {renderChildNode(child)}
            </Box>
          ))}
        </Box>
      </Box>
    );
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: subtreeWidth }}>
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
          ...orgNodeCardSx,
          cursor: canOpenUnitDetails ? 'pointer' : 'default',
          transition: canOpenUnitDetails ? 'border-color 0.16s ease, box-shadow 0.16s ease' : undefined,
          '&:hover': canOpenUnitDetails ? {
            borderColor: alpha(hierarchyPageColors.connector, 0.38),
            boxShadow: '0 4px 12px rgba(15, 23, 42, 0.08)',
          } : undefined,
        }}
      >
        <Stack spacing={1.15}>
          <Stack direction="row" spacing={1} justifyContent="space-between" alignItems="center">
            <Box sx={{ minWidth: 0 }}>
              <Typography
                sx={{
                  color: hierarchyPageColors.textPrimary,
                  fontSize: 14,
                  fontWeight: 600,
                  lineHeight: 1.24,
                  overflowWrap: 'anywhere',
                }}
              >
                {unit.name}
              </Typography>
            </Box>

            {canDelete ? (
              <Tooltip title="Удалить">
                <IconButton
                  size="small"
                  aria-label={`Удалить объединение ${unit.name}`}
                  onClick={(event) => {
                    event.stopPropagation();
                    onDelete(unit);
                  }}
                  sx={{ ...outlinedIconButtonSx, mr: -0.35, flexShrink: 0 }}
                >
                  <DeleteOutlineRoundedIcon sx={{ fontSize: 18 }} />
                </IconButton>
              </Tooltip>
            ) : null}
          </Stack>

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
                headerAction={showPrimaryActions && canOpenMemberDialog ? (
                  <Tooltip title="Добавить сотрудника">
                    <IconButton
                      size="small"
                      onClick={(event) => {
                        event.stopPropagation();
                        onOpenMemberDialog?.(unit);
                      }}
                      aria-label={`Добавить сотрудника в ${unit.name}`}
                      sx={outlinedIconButtonSx}
                    >
                      <GroupAddOutlinedIcon sx={{ fontSize: 17 }} />
                    </IconButton>
                  </Tooltip>
                ) : undefined}
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
          <Box
            sx={{
              position: 'relative',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
            }}
          >
            <Box sx={{ ...connectorLineSx, width: '2px', height: `${stemHeight}px` }} />

            {canCreateChild ? (
              <Box
                sx={{
                  position: 'relative',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  zIndex: 1,
                }}
              >
                <Tooltip title="Создать дочернюю группу">
                  <IconButton
                    aria-label={`Создать дочернюю группу в ${unit.name}`}
                    onClick={(event) => {
                      event.stopPropagation();
                      onOpenCreateChildDialog?.(unit);
                    }}
                    sx={{
                      width: 32,
                      height: 32,
                      bgcolor: 'primary.main',
                      color: '#ffffff',
                      boxShadow: hierarchyPageColors.shadow,
                      border: '3px solid #ffffff',
                      '&:hover': { bgcolor: 'primary.dark' },
                    }}
                  >
                    <AddRoundedIcon sx={{ fontSize: 20 }} />
                  </IconButton>
                </Tooltip>
                {hasChildren ? (
                  <Box sx={{ ...connectorLineSx, width: '2px', height: `${stemHeight}px` }} />
                ) : null}
              </Box>
            ) : null}
          </Box>

          {renderChildrenRow()}
        </Box>
      ) : null}
    </Box>
  );
};
